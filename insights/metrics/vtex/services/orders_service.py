from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from insights.sources.cache import CacheClient
from insights.sources.orders.clients import VtexOrdersRestClient
from insights.sources.vtexcredentials.clients import AuthRestClient as VtexAuthClient
from insights.sources.vtexcredentials.typing import VtexCredentialsDTO


class OrdersService:
    def __init__(self, project_uuid: str) -> None:
        self.project_uuid = project_uuid

    def _get_credentials(self) -> VtexCredentialsDTO:
        return VtexAuthClient(self.project_uuid).get_vtex_auth()

    def _get_client(self) -> VtexOrdersRestClient:
        return VtexOrdersRestClient(self._get_credentials(), CacheClient())

    def _get_past_dates(self, start_date, end_date):
        period = (end_date - start_date).days

        past_start_date = start_date - timedelta(days=period)
        past_end_date = end_date - timedelta(days=period)

        return past_start_date, past_end_date

    def _calculate_increase_percentage(self, past_value, current_value):
        return round(((current_value - past_value) / past_value) * 100, 2)

    def get_metrics_from_utm_source(self, utm_source, filters: dict) -> int:
        filters["utm_source"] = utm_source

        start_date = filters.pop("start_date")
        end_date = filters.pop("end_date")

        filters["ended_at__gte"] = start_date
        filters["ended_at__lte"] = end_date

        # for the current period:
        data = self._get_client().list(filters)
        current_value = data.get("accumulatedTotal")

        # for the past period:
        past_start_date, past_end_date = self._get_past_dates(start_date, end_date)

        filters["ended_at__gte"] = past_start_date
        filters["ended_at__lte"] = past_end_date

        past_data = self._get_client().list(filters)
        past_value = past_data.get("accumulatedTotal")

        response = {
            "utm_revenue": current_value,
            "utm_revenue_increase_percentage": self._calculate_increase_percentage(
                past_value, current_value
            ),
        }

        return response
