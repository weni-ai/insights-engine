from datetime import datetime
from typing import TYPE_CHECKING

from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
from insights.metrics.conversations.dataclass import ConversationsTimeseriesMetrics
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)

if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
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
