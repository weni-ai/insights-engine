from datetime import datetime
from uuid import UUID

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)


class MockConversationsMetricsService(BaseConversationsMetricsService):
    """
    Mock service for conversations metrics.
    """

    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            abandoned=ConversationsTotalsMetric(value=0, percentage=0),
        )
