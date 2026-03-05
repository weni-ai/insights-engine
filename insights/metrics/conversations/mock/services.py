from uuid import UUID
from datetime import datetime

from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.enums import (
    AvailableWidgetsListType,
    ConversationType,
    TopicsDistributionMetrics,
    SalesFunnelMetrics,
    AvailableWidgetsList,
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
        return {}

    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return {}

    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelMetrics:
        return {}

    def check_if_sales_funnel_data_exists(self, project_uuid: UUID) -> bool:
        return False

    def get_available_widgets(
        self, project_uuid: UUID, widget_type: AvailableWidgetsListType | None = None
    ) -> AvailableWidgetsList:
        return []

    def get_crosstab_data(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        return {}
