from uuid import UUID
from datetime import datetime

from insights.sources.flowruns.usecases import QueryExecutor as FlowRunsQueryExecutor
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

        # TODO: Check the correct filters names
        # TODO: Add all filters

        filters = {
            "created_on": {
                "gte": start_date,
                "lte": end_date,
            },
        }

        source_query = FlowRunsQueryExecutor(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        source_query.execute()
        return {}
