import logging
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from rest_framework import status
from sentry_sdk import capture_exception

from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


logger = logging.getLogger(__name__)


class UTMSourceMetricsUseCase:
    """
    Use case to get metrics from UTM source
    """

    def _convert_dates(
        self, start_date: date, end_date: date, project_tz: ZoneInfo
    ) -> tuple[datetime, datetime]:
        start_local = datetime.combine(start_date, time.min, tzinfo=project_tz)
        end_local = datetime.combine(
            end_date, time(23, 59, 59), tzinfo=project_tz
        )
        return (
            start_local.astimezone(timezone.utc),
            end_local.astimezone(timezone.utc),
        )

    def to_utc_range(
        self, start_date: date, end_date: date, project: Project
    ) -> tuple[datetime, datetime]:
        project_tz = ZoneInfo(project.timezone) if project.timezone else ZoneInfo("UTC")
        return self._convert_dates(start_date, end_date, project_tz)

    def execute(
        self, project: Project, utm_source: str, start_date: date, end_date: date
    ) -> tuple[int, dict]:
        start_dt, end_dt = self.to_utc_range(start_date, end_date, project)
        filters = {
            "project_uuid": str(project.uuid),
            "start_date": start_dt,
            "end_date": end_dt,
        }

        try:
            orders_service = OrdersService(project)
            orders_data = orders_service.get_metrics_from_utm_source(
                utm_source, filters
            )
            return status.HTTP_200_OK, orders_data

        except VtexCredentialsNotFound:
            logger.error(
                "[UTMSourceMetricsUseCase] VTEX credentials not found for project %s",
                project.uuid,
            )
            return status.HTTP_401_UNAUTHORIZED, {
                "error": (
                    "Unauthorized because VTEX credentials are not configured "
                    "or are invalid for this project"
                ),
            }
        except Exception as e:
            event_id = capture_exception(e)
            logger.error(
                "[UTMSourceMetricsUseCase] Error getting metrics from UTM source: %s", e
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {
                "error": "Failed to get metrics from UTM source",
                "event_id": event_id,
            }
