from datetime import datetime
from uuid import UUID
from insights.metrics.conversations.integrations.datalake.dataclass import (
    DatalakeConversationsTotalsMetric,
    DatalakeConversationsTotalsMetrics,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)


class MockConversationsMetricsService(BaseConversationsMetricsService):
    """
    Mock service for conversations metrics.
    """

    def get_conversations_totals(
        self, project: UUID, start_date: datetime, end_date: datetime
    ) -> DatalakeConversationsTotalsMetrics:
        return DatalakeConversationsTotalsMetrics(
            total_conversations=DatalakeConversationsTotalsMetric(
                value=100, percentage=100
            ),
            resolved=DatalakeConversationsTotalsMetric(value=60, percentage=60),
            unresolved=DatalakeConversationsTotalsMetric(value=40, percentage=40),
        )
