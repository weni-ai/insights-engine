import logging
from datetime import date, datetime

from rest_framework import status
from sentry_sdk import capture_exception

from insights.metrics.vtex.date_utils import to_utc_range
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


logger = logging.getLogger(__name__)


class UTMSourceMetricsUseCase:
    """
    Use case to get metrics from UTM source
    """

    def to_utc_range(
        self, start_date: date, end_date: date, project: Project
    ) -> tuple[datetime, datetime]:
        return to_utc_range(start_date, end_date, project)

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
