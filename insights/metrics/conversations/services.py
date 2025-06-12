from typing import TYPE_CHECKING
from datetime import datetime

from insights.metrics.conversations.dataclass import (
    ConversationTotalsMetrics,
    ConversationsTimeseriesMetrics,
)
from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
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

    def get_timeseries(
        cls,
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
