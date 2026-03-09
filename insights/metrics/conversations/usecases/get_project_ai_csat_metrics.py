import logging
from datetime import datetime
from uuid import UUID

from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.exceptions import (
    ConversationsMetricsError,
    GetProjectAiCsatMetricsError,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.widgets.models import Widget

logger = logging.getLogger(__name__)


class GetProjectAiCsatMetricsUseCase:
    """
    Use case to fetch project AI CSAT metrics.

    Builds the internal widget config, delegates to ConversationsMetricsService,
    and handles ConversationsMetricsError (logging, Sentry) by re-raising
    GetProjectAiCsatMetricsError with event_id for the HTTP layer.
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

        :raises GetProjectAiCsatMetricsError: when the service fails (includes event_id)
        """
        widget = Widget(
            config={
                "datalake_config": {
                    "agent_uuid": settings.CONVERSATIONS_DASHBOARD_NATIVE_CSAT_AGENT_UUID
                }
            }
        )

        try:
            return self.service.get_csat_metrics(
                project_uuid=project_uuid,
                widget=widget,
                start_date=start_date,
                end_date=end_date,
                metric_type=CsatMetricsType.AI,
            )
        except ConversationsMetricsError as e:
            event_id = capture_exception(e)
            logger.error(
                "[GetProjectAiCsatMetricsUseCase] Error getting project AI csat metrics: %s",
                e,
                exc_info=True,
            )
            raise GetProjectAiCsatMetricsError(
                str(e),
                event_id=event_id,
            ) from e
