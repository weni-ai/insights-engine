import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import pytz
from rest_framework import status

from sentry_sdk import capture_exception, capture_message

from insights.metrics.conversations.dataclass import (
    NPS,
    ConversationsTimeseriesMetrics,
    ConversationsTotalsMetrics,
    QueueMetric,
    RoomsByQueueMetric,
    SubjectMetricData,
    SubjectsMetrics,
    SubtopicMetrics,
    SubtopicTopicRelation,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    ConversationsMetricsResource,
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
    NPS_METRICS_MOCK_DATA,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
    DatalakeConversationsMetricsService,
)
from insights.sources.cache import CacheClient
from insights.sources.integrations.clients import NexusClient


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from datetime import date
    from insights.projects.models import Project


class ConversationsMetricsService(ConversationsServiceCachingMixin):
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        datalake_service: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
        nexus_client: NexusClient = NexusClient(),
        cache_client: CacheClient = CacheClient(),
        nexus_cache_ttl: int = 60,
    ):
        self.datalake_service = datalake_service
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.nexus_cache_ttl = nexus_cache_ttl

    def get_totals(
        self, project: "Project", start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations metrics totals
        """

        return self.datalake_service.get_conversations_totals(
            project_uuid=project.uuid,
            start_date=start_date,
            end_date=end_date,
        )

    def get_timeseries(
        cls,
        project: "Project",
        start_date: datetime,
        end_date: datetime,
        unit: ConversationsTimeseriesUnit,
    ) -> ConversationsTimeseriesMetrics:
        # Mock data for now
        return ConversationsTimeseriesMetrics(
            unit=unit,
            total=CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[unit]["total"],
            by_human=CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[unit]["by_human"],
        )

    def get_subjects_metrics(
        self,
        project_uuid: str,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationsSubjectsType,
        limit: int | None = None,
    ) -> SubjectsMetrics:
        """
        Get subjects metrics
        """
        # Mock data for now
        subjects = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])
        total_mock_subjects_qty = len(subjects)

        if limit is None:
            limit = total_mock_subjects_qty
            has_more = False
        else:
            has_more = limit < total_mock_subjects_qty

        subjects_to_show = [
            SubjectMetricData(
                name=subject.get("name"),
                percentage=subject.get("percentage"),
            )
            for subject in subjects[:limit]
        ]

        return SubjectsMetrics(
            has_more=has_more,
            subjects=subjects_to_show,
        )

    @classmethod
    def get_rooms_numbers_by_queue(
        cls,
        project: "Project",
        start_date: "date",
        end_date: "date",
        limit: int | None = None,
    ):
        """
        Get the rooms numbers by queue.
        """

        if project.timezone is None:
            tz = pytz.utc
        else:
            tz = pytz.timezone(project.timezone)

        # Create naive datetime at midnight in the project's timezone
        local_start = datetime.combine(start_date, datetime.min.time())
        local_end = datetime.combine(end_date, datetime.max.time())

        # Convert to UTC while preserving the intended local time
        start_datetime = tz.localize(local_start).astimezone(pytz.UTC)
        end_datetime = tz.localize(local_end).astimezone(pytz.UTC)

        queues = list(
            ChatsClient().get_rooms_numbers_by_queue(
                project.uuid,
                start_datetime,
                end_datetime,
            )
        )
        qty = len(queues)
        has_more = False

        queues_metrics = []
        total_rooms = sum(queue.rooms_number for queue in queues)

        queues_range = min(qty, limit) if limit else qty

        for queue in queues[:queues_range]:
            # Handle case where total_rooms is 0 to avoid ZeroDivisionError
            percentage = (
                0
                if total_rooms == 0
                else round(queue.rooms_number / total_rooms * 100, 2)
            )
            queues_metrics.append(
                QueueMetric(
                    name=queue.queue_name,
                    percentage=percentage,
                )
            )

        if limit and qty > limit:
            has_more = True

        return RoomsByQueueMetric(queues=queues_metrics, has_more=has_more)

    @classmethod
    def get_nps(
        cls,
        project: "Project",
        start_date: datetime.date,
        end_date: datetime.date,
        type: NPSType,
    ) -> NPS:
        """
        Get the NPS for a project
        """
        # Mock data for now
        return NPS(**NPS_METRICS_MOCK_DATA)

    def get_topics(self, project_uuid: UUID) -> dict:
        """
        Get conversation topics
        """

        if cached_results := self._get_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        ):
            return json.loads(cached_results)

        try:
            response = self.nexus_client.get_topics(project_uuid)

        except Exception as e:
            logger.error("Error fetching topics for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}. Event_id: {event_id}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )
            event_id = capture_message(
                f"Error fetching topics for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}. Event_id: {event_id}"
            )

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Get conversation subtopics
        """
        try:
            response = self.nexus_client.get_subtopics(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error fetching subtopics for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Error fetching subtopics for project {project_uuid}. Event_id: {event_id}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error fetching topics for project %s: %s", project_uuid, response.text
            )
            event_id = capture_message(
                f"Error fetching topics for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}. Event_id: {event_id}"
            )

        return response_content

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a conversation topic
        """
        try:
            response = self.nexus_client.create_topic(project_uuid, name, description)

        except Exception as e:
            logger.error("Error creating topic for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Error creating topic for project {project_uuid}. Event_id: {event_id}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error creating topic for project %s: %s", project_uuid, response.text
            )
            event_id = capture_message(
                f"Error creating topic for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error creating topic for project {project_uuid}"
            )

        self._clear_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        )

        return response_content

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> dict:
        """
        Create a conversation subtopic
        """

        try:
            response = self.nexus_client.create_subtopic(
                project_uuid, topic_uuid, name, description
            )

        except Exception as e:
            logger.error("Error creating subtopic for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)
            raise ConversationsMetricsError(
                f"Error creating subtopic for project {project_uuid}. Event_id: {event_id}"
            ) from e

        try:
            response_content = response.json()
        except Exception as e:
            logger.error("Error parsing topics for project %s: %s", project_uuid, e)
            response_content = response.text

        if not status.is_success(response.status_code):
            logger.error(
                "Error creating subtopic for project %s: %s",
                project_uuid,
                response.text,
            )
            event_id = capture_message(
                f"Error creating subtopic for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error creating subtopic for project {project_uuid}. Event_id: {event_id}"
            )

        self._clear_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        )

        return response_content

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Delete a conversation topic
        """

        try:
            response = self.nexus_client.delete_topic(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error deleting topic for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)
            raise ConversationsMetricsError(
                f"Error deleting topic for project {project_uuid}. Event_id: {event_id}"
            ) from e

        if not status.is_success(response.status_code):
            logger.error(
                "Error deleting topic for project %s: %s", project_uuid, response.text
            )
            event_id = capture_message(
                f"Error deleting topic for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error deleting topic for project {project_uuid}. Event_id: {event_id}"
            )

        self._clear_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        )

        return None

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> dict:
        """
        Delete a conversation subtopic
        """

        try:
            response = self.nexus_client.delete_subtopic(
                project_uuid, topic_uuid, subtopic_uuid
            )

        except Exception as e:
            logger.error("Error deleting subtopic for project %s: %s", project_uuid, e)
            event_id = capture_exception(e)
            raise ConversationsMetricsError(
                f"Error deleting subtopic for project {project_uuid}. Event_id: {event_id}"
            ) from e

        if not status.is_success(response.status_code):
            logger.error(
                "Error deleting subtopic for project %s: %s",
                project_uuid,
                response.text,
            )
            event_id = capture_message(
                f"Error deleting subtopic for project {project_uuid}: {response.text}"
            )

            raise ConversationsMetricsError(
                f"Error deleting subtopic for project {project_uuid}. Event_id: {event_id}"
            )

        self._clear_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS
        )

        return None

    def get_topics_distribution(
        self,
        project: "Project",
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        mock_data: bool = False,
    ) -> TopicsDistributionMetrics:
        """
        Get topics distribution
        """
        # If the topic distribution is limited by Nexus topics,
        # the client will see other topics listed as "OTHER"
        current_topics_data = self.get_topics(project.uuid)

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=subtopic.get("uuid"),
                subtopic_name=subtopic.get("name"),
                topic_uuid=topic.get("uuid"),
                topic_name=topic.get("name"),
            )
            for topic in current_topics_data
            for subtopic in topic["subtopic"]
        ]

        try:
            topics = self.datalake_service.get_topics_distribution(
                project_uuid=project.uuid,
                start_date=start_date,
                end_date=end_date,
                conversation_type=conversation_type,
                subtopics=subtopics,
                mock_data=mock_data,
            )
        except Exception as e:
            logger.error("Failed to get topics distribution", exc_info=True)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Failed to get topics distribution. Event ID: {event_id}"
            ) from e

        topics_metrics = []

        total_count = sum(topic_data.get("count", 0) for topic_data in topics.values())

        print("Topics", topics)

        for topic_uuid, topic_data in topics.items():
            subtopic_metrics = []
            topic_count = topic_data.get("count")
            for subtopic_uuid, subtopic_data in topic_data["subtopics"].items():
                subtopic_metrics.append(
                    SubtopicMetrics(
                        uuid=subtopic_uuid,
                        name=subtopic_data["name"],
                        quantity=subtopic_data["count"],
                        percentage=(
                            ((subtopic_data["count"] / topic_count) * 100)
                            if topic_count
                            else 0
                        ),
                    )
                )

            topics_metrics.append(
                TopicMetrics(
                    uuid=topic_uuid,
                    name=topic_data["name"],
                    quantity=topic_data["count"],
                    percentage=(
                        ((topic_data["count"] / total_count) * 100)
                        if total_count
                        else 0
                    ),
                    subtopics=subtopic_metrics,
                )
            )

        return TopicsDistributionMetrics(
            topics=topics_metrics,
        )
