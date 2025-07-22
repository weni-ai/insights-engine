from uuid import UUID
from datetime import datetime

from insights.metrics.conversations.enums import CsatMetricsType


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        metric_type: CsatMetricsType,
    ) -> dict:
        """
        Get csat metrics
        """
        # TODO
        return {}
