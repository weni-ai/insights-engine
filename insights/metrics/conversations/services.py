from uuid import UUID
from datetime import datetime


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
    ) -> dict:
        """
        Get csat metrics
        """

        pass
