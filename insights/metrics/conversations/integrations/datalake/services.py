from datetime import datetime
from uuid import UUID

from insights.metrics.conversations.integrations.datalake.dataclass import (
    DatalakeConversationsTotalsMetrics,
)
from insights.metrics.conversations.integrations.datalake.enums import (
    DatalakeConversationsClassification,
)


class DatalakeConversationsMetricsService:
    """
    Service for getting conversations metrics from Datalake.
    """

    def get_conversations_totals(
        self,
        project_uuid: UUID,
        classification: DatalakeConversationsClassification,
        start_date: datetime,
        end_date: datetime,
    ) -> DatalakeConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

        pass
