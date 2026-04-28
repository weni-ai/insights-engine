from datetime import datetime
from uuid import UUID

from django.conf import settings

from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.widgets.models import Widget


class GetProjectAiCsatMetricsUseCase:
    """
    Use case to fetch project AI CSAT metrics.

    Builds the internal widget config and delegates to ConversationsMetricsService.
    """

    def __init__(
        self,
        service: ConversationsMetricsService | None = None,
    ):
        self.service = service or ConversationsMetricsService()

    def execute(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Return AI CSAT metrics for the project in the given date range.
        """
        widget = Widget(
            config={
                "datalake_config": {
                    "agent_uuid": settings.CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID
                }
            }
        )

        return self.service.get_csat_metrics(
            project_uuid=project_uuid,
            widget=widget,
            start_date=start_date,
            end_date=end_date,
            metric_type=CsatMetricsType.AI,
        )
