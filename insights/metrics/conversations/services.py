from abc import ABC, abstractmethod
import logging
from typing import Callable, Optional
from uuid import UUID
from datetime import datetime
import json

from django.conf import settings
from sentry_sdk import capture_exception, capture_message
from rest_framework import status

from insights.metrics.conversations.dataclass import (
    AbsoluteNumbersMetrics,
    AgentInvocationAgent,
    AgentInvocationItem,
    AgentInvocationMetrics,
    AvailableWidgetsList,
    ConversationsTotalsMetrics,
    CrosstabItemData,
    CrosstabSubItemData,
    NPSMetrics,
    NPSMetricsField,
    SalesFunnelMetrics,
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.datalake.dataclass import (
    CrosstabSource,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
    DatalakeConversationsMetricsService,
)
from insights.metrics.conversations.mixins import ConversationsServiceCachingMixin
from insights.projects.parsers import parse_dict_to_json
from insights.sources.cache import CacheClient
from insights.sources.flowruns.usecases.query_execute import (
    QueryExecutor as FlowRunsQueryExecutor,
)
from insights.metrics.conversations.enums import (
    AbsoluteNumbersMetricsType,
    AvailableWidgets,
    AvailableWidgetsListType,
    ConversationType,
    ConversationsMetricsResource,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.sources.integrations.clients import (
    NexusConversationsAPIClient,
    BaseNexusConversationsAPIClient,
)
from insights.widgets.models import Widget


logger = logging.getLogger(__name__)


class BaseConversationsMetricsService(ABC):
    """
    Base class for conversations metrics services.
    """

    @abstractmethod
    def get_topics(self, project_uuid: UUID) -> dict:
        """
        Get conversation topics
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Get conversation subtopics
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a conversation topic
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> dict:
        """
        Create a conversation subtopic
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Delete a conversation topic
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> dict:
        """
        Delete a conversation subtopic
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        output_language: str = "en",
    ) -> TopicsDistributionMetrics:
        """
        Get topics distribution
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
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
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
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
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_generic_metrics_by_key(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get generic metrics by key
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelMetrics:
        """
        Get sales funnel data
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def check_if_sales_funnel_data_exists(self, project_uuid: UUID) -> bool:
        """
        Check if sales funnel data exists
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_available_widgets(
        self, project_uuid: UUID, widget_type: AvailableWidgetsListType | None = None
    ) -> AvailableWidgetsList:
        """
        Get available widgets
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_agent_invocations(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[AgentInvocationItem]:
        """
        Get agent invocation counts grouped by agent
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
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
        raise NotImplementedError("Subclasses must implement this method")


class ConversationsMetricsService(
    ConversationsServiceCachingMixin, BaseConversationsMetricsService
):
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        datalake_service: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
        nexus_conversations_client: BaseNexusConversationsAPIClient = NexusConversationsAPIClient(),
        cache_client: CacheClient = CacheClient(),
        nexus_conversations_cache_ttl: int = settings.NEXUS_CONVERSATIONS_CACHE_TTL,
        flowruns_query_executor: FlowRunsQueryExecutor = FlowRunsQueryExecutor,
    ):
        self.datalake_service: BaseDatalakeConversationsMetricsService = (
            datalake_service
        )
        self.nexus_conversations_client: BaseNexusConversationsAPIClient = (
            nexus_conversations_client
        )
        self.cache_client: CacheClient = cache_client
        self.nexus_conversations_cache_ttl: int = nexus_conversations_cache_ttl
        self.flowruns_query_executor: FlowRunsQueryExecutor = flowruns_query_executor

    def _convert_to_iso_string(self, date_value: datetime | str) -> str:
        """
        Convert datetime to ISO string if needed for JSON serialization
        """
        return (
            date_value.isoformat() if isinstance(date_value, datetime) else date_value
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
            response = self.nexus_conversations_client.get_topics(project_uuid)

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

        if isinstance(response_content, dict):
            results = response_content.get("results", [])
            next_url = response_content.get("next")
            page = 1
            max_pages = settings.NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES

            while next_url and page < max_pages:
                page += 1
                next_response = self.nexus_conversations_client.get_page(next_url)
                try:
                    next_content = next_response.json()
                except Exception:
                    break

                if not status.is_success(next_response.status_code):
                    break

                if isinstance(next_content, dict):
                    results.extend(next_content.get("results", []))
                    next_url = next_content.get("next")
                else:
                    break

            if next_url:
                logger.warning(
                    "Topics pagination limit reached for project %s. "
                    "There are still more pages to fetch (limit: %d).",
                    project_uuid,
                    max_pages,
                )

            topics_data = results
        else:
            if isinstance(response_content, list):
                topics_data = response_content
            else:
                topics_data = []

        self._save_cache_for_project_resource(
            project_uuid, ConversationsMetricsResource.TOPICS, topics_data
        )

        return topics_data

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        """
        Get conversation subtopics
        """
        try:
            response = self.nexus_conversations_client.get_subtopics(
                project_uuid, topic_uuid
            )

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

        if isinstance(response_content, dict):
            results = response_content.get("results", [])
            next_url = response_content.get("next")
            page = 1
            max_pages = settings.NEXUS_CONVERSATIONS_TOPICS_MAX_PAGES

            while next_url and page < max_pages:
                page += 1
                next_response = self.nexus_conversations_client.get_page(next_url)
                try:
                    next_content = next_response.json()
                except Exception:
                    break

                if not status.is_success(next_response.status_code):
                    break

                if isinstance(next_content, dict):
                    results.extend(next_content.get("results", []))
                    next_url = next_content.get("next")
                else:
                    break

            if next_url:
                logger.warning(
                    "Subtopics pagination limit reached for project %s, topic %s. "
                    "There are still more pages to fetch (limit: %d).",
                    project_uuid,
                    topic_uuid,
                    max_pages,
                )

            return results
        else:
            if isinstance(response_content, list):
                return response_content
            else:
                return []

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        """
        Create a conversation topic
        """
        try:
            response = self.nexus_conversations_client.create_topic(
                project_uuid, name, description
            )

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
            response = self.nexus_conversations_client.create_subtopic(
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
            response = self.nexus_conversations_client.delete_topic(
                project_uuid, topic_uuid
            )

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
            response = self.nexus_conversations_client.delete_subtopic(
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
        project_uuid: UUID,
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
        current_topics_data = self.get_topics(project_uuid)

        try:
            topics = self.datalake_service.get_topics_distribution(
                project_uuid=project_uuid,
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

    def get_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations metrics totals
        """

        return self.datalake_service.get_conversations_totals(
            project_uuid=project_uuid,
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
            "created_on__gte": self._convert_to_iso_string(start_date),
            "created_on__lte": self._convert_to_iso_string(end_date),
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
            promoters=NPSMetricsField(count=promoters, percentage=promoters_percentage),
            passives=NPSMetricsField(count=passives, percentage=passives_percentage),
            detractors=NPSMetricsField(
                count=detractors, percentage=detractors_percentage
            ),
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
            "created_on__gte": self._convert_to_iso_string(start_date),
            "created_on__lte": self._convert_to_iso_string(end_date),
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

    def check_if_sales_funnel_data_exists(self, project_uuid: UUID) -> bool:
        """
        Check if sales funnel data exists in Datalake.
        """
        return self.datalake_service.check_if_sales_funnel_data_exists(project_uuid)

    def _get_native_available_widgets(
        self, project_uuid: UUID
    ) -> list[AvailableWidgets]:
        """
        Get native available widgets.
        """
        available_widgets = []

        if self.check_if_sales_funnel_data_exists(project_uuid):
            available_widgets.append(AvailableWidgets.SALES_FUNNEL)

        return available_widgets

    def get_available_widgets(
        self, project_uuid: UUID, widget_type: AvailableWidgetsListType | None = None
    ) -> AvailableWidgetsList:
        """
        Get available widgets.
        """
        available_widgets = []

        if widget_type == AvailableWidgetsListType.NATIVE or widget_type is None:
            native_available_widgets = self._get_native_available_widgets(project_uuid)
            available_widgets.extend(native_available_widgets)

        return AvailableWidgetsList(available_widgets=available_widgets)

    def _validate_crosstab_source(self, source: str) -> CrosstabSource:
        """
        Validate crosstab source
        """
        key = source.get("key")
        field = source.get("field")

        if field is None or field == "":
            field = "value"

        if not key:
            raise ConversationsMetricsError("Key is required")

        return CrosstabSource(key=key, field=field)

    def _validate_crosstab_widget(
        self, widget: Widget
    ) -> tuple[CrosstabSource, CrosstabSource, str | None]:
        """
        Validate crosstab widget
        """
        if (
            widget.type != "conversations.crosstab"
            or widget.source != "conversations.crosstab"
        ):
            raise ConversationsMetricsError("Widget type or source is not valid")

        config = widget.config or {}

        source_a = self._validate_crosstab_source(config.get("source_a", {}))
        source_b = self._validate_crosstab_source(config.get("source_b", {}))
        reference_field = config.get("reference_field") or None

        return source_a, source_b, reference_field

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
        source_a, source_b, reference_field = self._validate_crosstab_widget(widget)

        data = self.datalake_service.get_crosstab_data(
            project_uuid,
            source_a,
            source_b,
            start_date,
            end_date,
            reference_field=reference_field,
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

    def get_agent_invocations(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> AgentInvocationMetrics:
        """
        Get agent invocation counts grouped by agent
        """
        invocations = self.datalake_service.get_agent_invocations(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        total_count = sum(item.count for item in invocations.values())

        return AgentInvocationMetrics(
            invocations=[
                AgentInvocationItem(
                    label=label,
                    agent=(
                        AgentInvocationAgent(uuid=item.agent_uuid)
                        if item.agent_uuid
                        else None
                    ),
                    value=(
                        round((item.count / total_count) * 100, 2)
                        if total_count
                        else 0
                    ),
                    full_value=item.count,
                )
                for label, item in invocations.items()
            ],
            total=total_count,
        )

    def get_event_count(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> int:
        """
        Get event count from Datalake.
        """

        return self.datalake_service.get_event_count(
            project_uuid, event_name, start_date, end_date, key, agent_uuid
        )

    def get_events_values_sum(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> int:
        """
        Get events values sum from Datalake.
        """

        return self.datalake_service.get_events_values_sum(
            project_uuid, event_name, start_date, end_date, key, agent_uuid, field_name
        )

    def get_events_values_average(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> int:
        """
        Get events values average from Datalake.
        """

        return self.datalake_service.get_events_values_average(
            project_uuid, event_name, start_date, end_date, key, agent_uuid, field_name
        )

    def get_events_highest_value(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> int:
        """
        Get events highest value from Datalake.
        """

        return self.datalake_service.get_events_highest_value(
            project_uuid, event_name, start_date, end_date, key, agent_uuid, field_name
        )

    def get_events_lowest_value(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> int:
        """
        Get events lowest value from Datalake.
        """

        return self.datalake_service.get_events_lowest_value(
            project_uuid, event_name, start_date, end_date, key, agent_uuid, field_name
        )

    def _get_absolute_numbers_method_by_operation(
        self, operation: AbsoluteNumbersMetricsType
    ) -> Callable:
        """
        Get absolute numbers method by operation
        """
        operation_mapping = {
            AbsoluteNumbersMetricsType.TOTAL: self.get_event_count,
            AbsoluteNumbersMetricsType.SUM: self.get_events_values_sum,
            AbsoluteNumbersMetricsType.AVERAGE: self.get_events_values_average,
            AbsoluteNumbersMetricsType.HIGHEST: self.get_events_highest_value,
            AbsoluteNumbersMetricsType.LOWEST: self.get_events_lowest_value,
        }

        return operation_mapping.get(operation)

    def get_absolute_numbers(
        self,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get absolute numbers metrics
        """

        config = widget.config or {}
        operation = config.get("operation")
        key = config.get("key")
        agent_uuid = config.get("agent_uuid")
        field_name = config.get("value_field_name")

        if field_name == "":
            field_name = None

        assert operation is not None
        assert key is not None
        assert agent_uuid is not None

        method = self._get_absolute_numbers_method_by_operation(operation)

        project_uuid = (
            widget.parent.dashboard.project_id
            if widget.parent
            else widget.dashboard.project_id
        )

        value = method(
            project_uuid=project_uuid,
            key=key,
            start_date=start_date,
            end_date=end_date,
            agent_uuid=agent_uuid,
            field_name=field_name,
            event_name="weni_nexus_data",
        )

        return AbsoluteNumbersMetrics(value=value)
