from typing import TYPE_CHECKING
from datetime import datetime


from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
    DatalakeConversationsMetricsService,
)

if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        datalake_client: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
    ):
        self.datalake_client = datalake_client

    def get_totals(
        self, project: "Project", start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations metrics totals
        """

        return self.datalake_client.get_conversations_totals(
            project=project,
            start_date=start_date,
            end_date=end_date,
        )
