import logging
from typing import TYPE_CHECKING
from uuid import UUID
from datetime import datetime
import json

from sentry_sdk import capture_exception, capture_message
from rest_framework import status

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetrics,
    SubtopicMetrics,
    SubtopicTopicRelation,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
    DatalakeConversationsMetricsService,
)
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
from insights.projects.parsers import parse_dict_to_json
from insights.sources.cache import CacheClient
from insights.sources.flowruns.usecases.query_execute import (
    QueryExecutor as FlowRunsQueryExecutor,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    ConversationsMetricsResource,
    CsatMetricsType,
)
from insights.sources.integrations.clients import NexusClient
from insights.widgets.models import Widget


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
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
        flowruns_query_executor: FlowRunsQueryExecutor = FlowRunsQueryExecutor,
    ):
        self.datalake_service = datalake_service
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.nexus_cache_ttl = nexus_cache_ttl
        self.flowruns_query_executor = flowruns_query_executor

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
            )
        except Exception as e:
            logger.error("Failed to get topics distribution", exc_info=True)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Failed to get topics distribution. Event ID: {event_id}"
            ) from e

        topics_metrics = []

        total_count = sum(topic_data.get("count", 0) for topic_data in topics.values())

        for topic_uuid, topic_data in topics.items():
            subtopic_metrics = []
            topic_count = topic_data.get("count")
            for subtopic_uuid, subtopic_data in topic_data["subtopics"].items():
                subtopic_metrics.append(
                    SubtopicMetrics(
                        uuid=subtopic_uuid,
                        name=subtopic_data.get("name"),
                        quantity=subtopic_data.get("count"),
                        percentage=(
                            ((subtopic_data.get("count") / topic_count) * 100)
                            if topic_count
                            else 0
                        ),
                    )
                )

            topics_metrics.append(
                TopicMetrics(
                    uuid=topic_uuid,
                    name=topic_data.get("name"),
                    quantity=topic_data.get("count"),
                    percentage=(
                        ((topic_data.get("count") / total_count) * 100)
                        if total_count
                        else 0
                    ),
                    subtopics=subtopic_metrics,
                )
            )

        return TopicsDistributionMetrics(
            topics=topics_metrics,
        )

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

    def _get_csat_metrics_from_flowruns(
        self,
        flow_uuid: UUID,
        project_uuid: UUID,
        op_field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        filters = {
            "modified_on": {
                "gte": start_date,
                "lte": end_date,
            },
            "flow": flow_uuid,
        }

        return self.flowruns_query_executor.execute(
            filters,
            operation="recurrence",
            parser=parse_dict_to_json,
            query_kwargs={
                "project": project_uuid,
                "op_field": op_field,
            },
        )

    def _get_csat_metrics_from_datalake(
        self,
        project_uuid: UUID,
        agent_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        # TODO
        metrics = self.datalake_service.get_csat_metrics(
            project_uuid, agent_uuid, start_date, end_date
        )

        total_count = sum(metrics.values())

        results = {
            "results": [
                {
                    "label": score,
                    "value": round((score_count / total_count) * 100, 2),
                    "full_value": score_count,
                }
                for score, score_count in metrics.items()
            ]
        }

        return results

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
        metric_type: CsatMetricsType,
    ) -> dict:
        """
        Get csat metrics
        """
        # HUMAN
        if metric_type == CsatMetricsType.HUMAN:
            flow_uuid = widget.config.get("filter", {}).get("flow")
            op_field = widget.config.get("op_field")

            if not flow_uuid:
                raise ConversationsMetricsError(
                    "Flow UUID is required in the widget config"
                )

            if not op_field:
                raise ConversationsMetricsError(
                    "Op field is required in the widget config"
                )

            return self._get_csat_metrics_from_flowruns(
                flow_uuid, project_uuid, op_field, start_date, end_date
            )

        # AI
        agent_uuid = (
            widget.config.get("filter", {}).get("datalake_config", {}).get("agent_uuid")
        )

        if not agent_uuid:
            raise ConversationsMetricsError(
                "Agent UUID is required in the widget config"
            )

        return self._get_csat_metrics_from_datalake(
            project_uuid, agent_uuid, start_date, end_date
        )
