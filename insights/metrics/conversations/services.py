from typing import TYPE_CHECKING
from datetime import datetime

from insights.metrics.conversations.dataclass import ConversationTotalsMetrics
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
)

if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_totals(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> ConversationTotalsMetrics:
        """
        Get conversations metrics totals
        """
        # Mock data for now

        return ConversationTotalsMetrics.from_values(
            by_ai=CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"],
            by_human=CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )
