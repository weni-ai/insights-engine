import logging
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from dateutil.parser import parse as date_parser
from rest_framework import status
from sentry_sdk import capture_exception

from insights.metrics.vtex.date_utils import (
    iter_period_keys,
    period_key_for,
    to_utc_range,
)
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


logger = logging.getLogger(__name__)


class OrderValuesByPeriodUseCase:
    def to_utc_range(
        self, start_date: date, end_date: date, project: Project
    ) -> tuple[datetime, datetime]:
        return to_utc_range(start_date, end_date, project)

    def _project_tz(self, project: Project) -> ZoneInfo:
        return ZoneInfo(project.timezone) if project.timezone else ZoneInfo("UTC")

    def _order_local_date(
        self, authorized_date: str, project_tz: ZoneInfo
    ) -> date | None:
        try:
            parsed = date_parser(authorized_date)
        except (TypeError, ValueError):
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(project_tz).date()

    def execute(
        self,
        project: Project,
        utm_source: str,
        start_date: date,
        end_date: date,
        granularity: str,
        week_starts_on: str,
    ) -> tuple[int, dict]:
        start_dt, end_dt = self.to_utc_range(start_date, end_date, project)
        filters = {
            "project_uuid": str(project.uuid),
            "start_date": start_dt,
            "end_date": end_dt,
        }

        try:
            orders_data = OrdersService(project).get_orders_from_utm_source(
                utm_source, filters
            )
            return status.HTTP_200_OK, self._build_response(
                project,
                orders_data,
                start_date,
                end_date,
                granularity,
                week_starts_on,
            )
        except VtexCredentialsNotFound:
            logger.error(
                "[OrderValuesByPeriodUseCase] VTEX credentials not found for project %s",
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
                "[OrderValuesByPeriodUseCase] Error getting order values by period: %s",
                e,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {
                "error": "Failed to get order values by period",
                "event_id": event_id,
            }

    def _build_response(
        self,
        project: Project,
        orders_data: dict,
        start_date: date,
        end_date: date,
        granularity: str,
        week_starts_on: str,
    ) -> dict:
        project_tz = self._project_tz(project)
        period_keys = iter_period_keys(
            start_date, end_date, granularity, week_starts_on
        )
        totals: dict[date, int] = {key: 0 for key in period_keys}
        currency = orders_data.get("currency_code") or None

        for order in orders_data.get("orders", []):
            local_date = self._order_local_date(
                order.get("authorized_date"), project_tz
            )
            if local_date is None or local_date < start_date or local_date > end_date:
                continue

            key = period_key_for(local_date, granularity, week_starts_on)
            if key not in totals:
                continue

            totals[key] += order.get("total_value") or 0
            currency = order.get("currency_code") or currency

        return {
            "currency": currency,
            "results": [
                {key.isoformat(): {"value": round(totals[key] / 100, 2)}}
                for key in period_keys
            ],
        }
