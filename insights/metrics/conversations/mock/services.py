from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from insights.metrics.conversations.dataclass import (
    AgentInvocationAgent,
    AgentInvocationItem,
    AgentInvocationMetrics,
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    NPSMetrics,
    NPSMetricsField,
    SubtopicMetrics,
    ToolResultAgent,
    ToolResultItem,
    ToolResultMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
    SalesFunnelMetrics,
    AvailableWidgetsList,
)
from insights.metrics.conversations.enums import (
    AvailableWidgetsListType,
    ConversationType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.widgets.models import Widget
from insights.metrics.conversations.services import BaseConversationsMetricsService


class MockConversationsMetricsService(BaseConversationsMetricsService):
    def get_topics(self, project_uuid: UUID) -> dict:
        return {}

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        return {}

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        return {}

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> dict:
        return {}

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        return {}

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> dict:
        return {}

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        output_language: str = "en",
    ) -> TopicsDistributionMetrics:
        return TopicsDistributionMetrics(
            topics=[
                TopicMetrics(
                    uuid=uuid4(),
                    name="Topic 1",
                    quantity=120,
                    percentage=50.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=uuid4(),
                            name="Subtopic 1.1",
                            quantity=50,
                            percentage=100.0,
                        ),
                    ],
                ),
                TopicMetrics(
                    uuid=uuid4(),
                    name="Topic 2",
                    quantity=100,
                    percentage=50.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=uuid4(),
                            name="Subtopic 2.1",
                            quantity=65,
                            percentage=65.0,
                        ),
                        SubtopicMetrics(
                            uuid=uuid4(),
                            name="Subtopic 2.2",
                            quantity=35,
                            percentage=35.0,
                        ),
                    ],
                ),
            ]
        )

    def get_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
        )

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
        metric_type: CsatMetricsType,
    ) -> dict:
        scores = {"1": 10, "2": 20, "3": 30, "4": 40, "5": 50}
        total_count = sum(scores.values())
        return {
            "results": [
                {
                    "label": label,
                    "value": round((score / total_count) * 100, 2),
                    "full_value": score,
                }
                for label, score in scores.items()
            ]
        }

    def get_nps_metrics(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
        metric_type: NpsMetricsType,
    ) -> dict:
        scores = {"1": 10, "2": 20, "3": 30, "4": 40, "5": 50}
        total_count = sum(scores.values())

        promoters = scores.get("10", 0) + scores.get("9", 0)
        passives = scores.get("8", 0) + scores.get("7", 0)
        detractors = sum(scores.get(str(i), 0) for i in range(7))
        score = (promoters - detractors) / total_count * 100

        promoters_percentage = (promoters / total_count) * 100
        passives_percentage = (passives / total_count) * 100
        detractors_percentage = (detractors / total_count) * 100

        return NPSMetrics(
            total_responses=total_count,
            promoters=NPSMetricsField(count=promoters, percentage=promoters_percentage),
            passives=NPSMetricsField(count=passives, percentage=passives_percentage),
            detractors=NPSMetricsField(
                count=detractors, percentage=detractors_percentage
            ),
            score=score,
        )

    def get_generic_metrics_by_key(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        return {}

    def get_agent_invocations(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> AgentInvocationMetrics:
        agent_uuid = str(uuid4())
        invocations = [
            AgentInvocationItem(
                label="invocation_1",
                agent=AgentInvocationAgent(uuid=agent_uuid),
                value=66.67,
                full_value=20,
            ),
            AgentInvocationItem(
                label="invocation_2",
                agent=None,
                value=33.33,
                full_value=10,
            ),
        ]
        return AgentInvocationMetrics(
            invocations=invocations,
            total=30,
        )

    def get_tool_results(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> ToolResultMetrics:
        agent_uuid = str(uuid4())
        tool_results = [
            ToolResultItem(
                label="tool_result_1",
                agent=ToolResultAgent(uuid=agent_uuid),
                value=66.67,
                full_value=20,
            ),
            ToolResultItem(
                label="tool_result_2",
                agent=None,
                value=33.33,
                full_value=10,
            ),
        ]
        return ToolResultMetrics(
            tool_results=tool_results,
            total=30,
        )

    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelMetrics:
        return SalesFunnelMetrics(
            leads_count=150,
            total_orders_count=45,
            total_orders_value=675000,
            currency_code="USD",
        )

    def check_if_sales_funnel_data_exists(self, project_uuid: UUID) -> bool:
        return False

    def get_available_widgets(
        self, project_uuid: UUID, widget_type: AvailableWidgetsListType | None = None
    ) -> AvailableWidgetsList:
        return []

    def get_crosstab_data(
        self,
        project_uuid: UUID,
        event_name: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
        agent_uuid: str,
        field_name: Optional[str] = None,
    ) -> dict:
        return {}

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
        return 0

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
        return 0

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
        return 0

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
        return 0

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
        return 0

    def get_absolute_numbers(
        self,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        return {}
