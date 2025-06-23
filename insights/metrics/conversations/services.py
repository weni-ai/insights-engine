import datetime
from typing import TYPE_CHECKING

from insights.metrics.conversations.tests.mock import NPS_METRICS_MOCK_DATA
from insights.metrics.conversations.dataclass import NPS


if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_nps(
        cls, project: "Project", start_date: datetime.date, end_date: datetime.date
    ) -> NPS:
        """
        Get the NPS for a project
        """
        # Mock data for now
        return NPS(**NPS_METRICS_MOCK_DATA)
