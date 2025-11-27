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
    ConversationsTotalsMetrics,
    CrosstabItemData,
    CrosstabSubItemData,
    NPSMetrics,
    SalesFunnelMetrics,
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
    NPSMetrics,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.datalake.dataclass import (
    CrosstabSource,
)
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
    NpsMetricsType,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
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

        print("get totals (metrics service)")
        print("start_date", start_date)
        print("end_date", end_date)

        return self.datalake_service.get_conversations_totals(
            project_uuid=project.uuid,
            start_date=start_date,
            end_date=end_date,
        )

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
        output_language: str = "en",
    ) -> TopicsDistributionMetrics:
        """
        Get topics distribution
        """
        # If the topic distribution is limited by Nexus topics,
        # the client will see other topics listed as "OTHER"
        current_topics_data = self.get_topics(project.uuid)

        try:
            topics = self.datalake_service.get_topics_distribution(
                project_uuid=project.uuid,
                start_date=start_date,
                end_date=end_date,
                conversation_type=conversation_type,
                current_topics_data=current_topics_data,
                output_language=output_language,
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
                            round(((subtopic_data.get("count") / topic_count) * 100), 2)
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
                        round(((topic_data.get("count") / total_count) * 100), 2)
                        if total_count
                        else 0
                    ),
                    subtopics=subtopic_metrics,
                )
            )

        return TopicsDistributionMetrics(
            topics=topics_metrics,
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

        promoters_percentage = (
            round((promoters / total_responses) * 100, 2) if total_responses else 0
        )
        passives_percentage = (
            round((passives / total_responses) * 100, 2) if total_responses else 0
        )
        detractors_percentage = (
            round((detractors / total_responses) * 100, 2) if total_responses else 0
        )

        score = round(
            (promoters - detractors) / total_responses * 100 if total_responses else 0,
            2,
        )

        return NPSMetrics(
            total_responses=total_responses,
            promoters=promoters_percentage,
            passives=passives_percentage,
            detractors=detractors_percentage,
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

    def get_sales_funnel_data(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> SalesFunnelMetrics:
        """
        Get sales funnel data
        """
        data = self.datalake_service.get_sales_funnel_data(
            project_uuid, start_date, end_date
        )

        return SalesFunnelMetrics(
            leads_count=data.leads_count,
            total_orders_count=data.total_orders_count,
            total_orders_value=data.total_orders_value,
            currency_code=data.currency_code,
        )

    def _validate_crosstab_source(self, source: str) -> CrosstabSource:
        """
        Validate crosstab source
        """
        key = source.get("key")
        field = source.get("field", "value")

        if not key:
            raise ConversationsMetricsError("Key is required")

        return CrosstabSource(key=key, field=field)

    def _validate_crosstab_widget(self, widget: Widget) -> None:
        """
        Validate crosstab widget
        """
        if (
            widget.type != "conversation.crosstab"
            or widget.source != "conversation.crosstab"
        ):
            raise ConversationsMetricsError("Widget type or source is not valid")

        config = widget.config or {}

        source_a = self._validate_crosstab_source(config.get("source_a", {}))
        source_b = self._validate_crosstab_source(config.get("source_b", {}))

        return source_a, source_b

    def get_crosstab_data(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get crosstab data
        """
        source_a, source_b = self._validate_crosstab_widget(widget)

        data = self.datalake_service.get_crosstab_data(
            project_uuid, source_a, source_b, start_date, end_date
        )

        items: list[CrosstabItemData] = []

        for label, item in data.items():
            total = sum(item.values())
            subitems: list[CrosstabSubItemData] = []

            for subitem_label, count in item.items():
                subitems.append(
                    CrosstabSubItemData(
                        title=subitem_label,
                        count=count,
                        percentage=round((count / total) * 100, 2) if total else 0,
                    )
                )

            items.append(
                CrosstabItemData(
                    title=label,
                    total=total,
                    subitems=subitems,
                )
            )

        return items
