import json
from datetime import datetime
import logging
from typing import TYPE_CHECKING
from uuid import UUID

import pytz
from rest_framework import status

from sentry_sdk import capture_exception, capture_message
from insights.projects.parsers import parse_dict_to_json

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
    NPSMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    ConversationsMetricsResource,
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
    CsatMetricsType,
    NpsMetricsType,
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
from insights.sources.flowruns.usecases.query_execute import (
    QueryExecutor as FlowRunsQueryExecutor,
)
from insights.sources.integrations.clients import NexusClient
from insights.widgets.models import Widget


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
        flowruns_query_executor: FlowRunsQueryExecutor = FlowRunsQueryExecutor,
    ):
        self.datalake_service = datalake_service
        self.nexus_client = nexus_client
        self.cache_client = cache_client
        self.nexus_cache_ttl = nexus_cache_ttl
        self.flowruns_query_executor = flowruns_query_executor

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
        self,
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

        total_count = (
            sum(topic_data.get("count", 0) for topic_data in topics.values())
            if topics
            else 0
        )

        print("Topics", topics)

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
        metrics = self.datalake_service.get_csat_metrics(
            project_uuid, agent_uuid, start_date, end_date
        )

        total_count = sum(metrics.values())

        results = {
            "results": [
                {
                    "label": score,
                    "value": (
                        round((score_count / total_count) * 100, 2)
                        if total_count
                        else 0
                    ),
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
                event_id = capture_message("Flow UUID is required in the widget config")

                raise ConversationsMetricsError(
                    f"Flow UUID is required in the widget config. Event ID: {event_id}"
                )

            if not op_field:
                event_id = capture_message("Op field is required in the widget config")

                raise ConversationsMetricsError(
                    f"Op field is required in the widget config. Event ID: {event_id}"
                )

            return self._get_csat_metrics_from_flowruns(
                flow_uuid, project_uuid, op_field, start_date, end_date
            )

        # AI
        agent_uuid = widget.config.get("datalake_config", {}).get("agent_uuid")

        if not agent_uuid:
            raise ConversationsMetricsError(
                "Agent UUID is required in the widget config"
            )

        return self._get_csat_metrics_from_datalake(
            project_uuid, agent_uuid, start_date, end_date
        )

    def _transform_nps_results(self, results: dict) -> NPSMetrics:
        """
        Apply NPS methodology to the results

        https://www.salesforce.com/eu/learning-centre/customer-service/calculate-net-promoter-score/
        """

        total_responses = sum(results.get(str(i), 0) for i in range(11))
        promoters = results.get("10", 0) + results.get("9", 0)
        passives = results.get("8", 0) + results.get("7", 0)
        detractors = sum(results.get(str(i), 0) for i in range(7))

        score = round(
            (promoters - detractors) / total_responses * 100 if total_responses else 0,
            2,
        )

        return NPSMetrics(
            total_responses=total_responses,
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            score=score,
        )

    def _get_nps_metrics_from_flowruns(
        self,
        flow_uuid: UUID,
        project_uuid: UUID,
        op_field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get nps metrics from flowruns
        """
        filters = {
            "modified_on": {
                "gte": start_date,
                "lte": end_date,
            },
            "flow": flow_uuid,
        }

        results = self.flowruns_query_executor.execute(
            filters,
            operation="recurrence",
            parser=parse_dict_to_json,
            query_kwargs={
                "project": project_uuid,
                "op_field": op_field,
            },
        )

        assert "results" in results, "Results must contain a 'results' key"
        assert isinstance(results["results"], list), "Results must be a list"

        results_counts = {
            result.get("label"): result.get("full_value", 0)
            for result in results["results"]
        }

        return self._transform_nps_results(results_counts)

    def _get_nps_metrics_from_datalake(
        self,
        project_uuid: UUID,
        agent_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get nps metrics from datalake
        """

        results = self.datalake_service.get_nps_metrics(
            project_uuid, agent_uuid, start_date, end_date
        )

        return self._transform_nps_results(results)

    def get_nps_metrics(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
        metric_type: NpsMetricsType,
    ) -> dict:
        """
        Get nps metrics
        """
        # HUMAN
        if metric_type == NpsMetricsType.HUMAN:
            flow_uuid = widget.config.get("filter", {}).get("flow")
            op_field = widget.config.get("op_field")

            if not flow_uuid:
                event_id = capture_message("Flow UUID is required in the widget config")

                raise ConversationsMetricsError(
                    f"Flow UUID is required in the widget config. Event ID: {event_id}"
                )

            if not op_field:
                event_id = capture_message("Op field is required in the widget config")

                raise ConversationsMetricsError(
                    f"Op field is required in the widget config. Event ID: {event_id}"
                )

            return self._get_nps_metrics_from_flowruns(
                flow_uuid, project_uuid, op_field, start_date, end_date
            )

        # AI
        agent_uuid = widget.config.get("datalake_config", {}).get("agent_uuid")

        if not agent_uuid:
            event_id = capture_message("Agent UUID is required in the widget config")

            raise ConversationsMetricsError(
                f"Agent UUID is required in the widget config. Event ID: {event_id}"
            )

        return self._get_nps_metrics_from_datalake(
            project_uuid, agent_uuid, start_date, end_date
        )

    def get_generic_metrics_by_key(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ):
        """
        Get generic metrics by key
        """
        agent_uuid = widget.config.get("datalake_config", {}).get("agent_uuid")

        if not agent_uuid:
            raise ConversationsMetricsError(
                "Agent UUID is required in the widget config"
            )

        key = widget.config.get("datalake_config", {}).get("key")

        if not key:
            raise ConversationsMetricsError("Key is required in the widget config")

        metrics = self.datalake_service.get_generic_metrics_by_key(
            project_uuid, agent_uuid, start_date, end_date, key
        )

        total_count = sum(metrics.values())

        results = {
            "results": [
                {
                    "label": score,
                    "value": (
                        round((score_count / total_count) * 100, 2)
                        if total_count
                        else 0
                    ),
                    "full_value": score_count,
                }
                for score, score_count in metrics.items()
            ]
        }

        return results
