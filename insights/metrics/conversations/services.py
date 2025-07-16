import json
from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID
import logging
from sentry_sdk import capture_message

import pytz

from insights.metrics.conversations.dataclass import (
    NPS,
    QueueMetric,
    RoomsByQueueMetric,
    ConversationsTotalsMetrics,
    ConversationsTimeseriesMetrics,
    SubjectGroup,
    SubjectItem,
    SubjectMetricData,
    SubjectsDistributionMetrics,
    SubjectsMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationsMetricsResource,
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA,
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
        datalake_client: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
        nexus_client: NexusClient = NexusClient(),
        cache_client: CacheClient = CacheClient(),
        nexus_cache_ttl: int = 60,
    ):
        self.datalake_client = datalake_client
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.nexus_cache_ttl = nexus_cache_ttl

    def get_totals(
        self, project: "Project", start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations metrics totals
        """

        return self.datalake_client.get_conversations_totals(
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
    def get_subjects_distribution(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> SubjectsDistributionMetrics:
        # Mock data for now
        groups = []
        for group in CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA["groups"]:
            subjects = []
            for subject in group["subjects"]:
                subjects.append(
                    SubjectItem(name=subject["name"], percentage=subject["percentage"])
                )
            groups.append(
                SubjectGroup(
                    name=group["name"],
                    percentage=group["percentage"],
                    subjects=subjects,
                )
            )
        return SubjectsDistributionMetrics(groups=groups)

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

    def get_topics(self, project_uuid: UUID) -> tuple[dict, int]:
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
            capture_message("Error fetching topics for project %s: %s", project_uuid, e)

            raise ConversationsMetricsError(
                f"Error fetching topics for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> tuple[dict, int]:
        """
        Get conversation subtopics
        """

        if cached_results := self._get_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS
        ):
            return json.loads(cached_results)

        try:
            response = self.nexus_client.get_subtopics(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error fetching subtopics for project %s: %s", project_uuid, e)
            capture_message(
                "Error fetching subtopics for project %s: %s", project_uuid, e
            )

            raise ConversationsMetricsError(
                f"Error fetching subtopics for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )

        return response_content

    def create_topic(
        self, project_uuid: UUID, name: str, description: str
    ) -> tuple[dict, int]:
        """
        Create a conversation topic
        """
        try:
            response = self.nexus_client.create_topic(project_uuid, name, description)

        except Exception as e:
            logger.error("Error creating topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error creating topic for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> tuple[dict, int]:
        """
        Create a conversation subtopic
        """

        try:
            response = self.nexus_client.delete_topic(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error deleting topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error creating subtopic for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )

        return response_content

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> tuple[dict, int]:
        """
        Delete a conversation topic
        """

        try:
            response = self.nexus_client.delete_topic(project_uuid, topic_uuid)

        except Exception as e:
            logger.error("Error deleting topic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error deleting topic for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, response_content
        )

        return response_content

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> tuple[dict, int]:
        """
        Delete a conversation subtopic
        """

        try:
            response = self.nexus_client.delete_subtopic(
                project_uuid, topic_uuid, subtopic_uuid
            )

        except Exception as e:
            logger.error("Error deleting subtopic for project %s: %s", project_uuid, e)
            raise ConversationsMetricsError(
                f"Error deleting subtopic for project {project_uuid}"
            ) from e

        response_content = response.json()

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.SUBTOPICS, response_content
        )
