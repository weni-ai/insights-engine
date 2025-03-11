from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from insights.internals.base import InternalAuthentication
from insights.projects.models import Project
from insights.sources.cache import CacheClient
from insights.sources.orders.clients import VtexOrdersRestClient
from insights.sources.vtexcredentials.clients import AuthRestClient as VtexAuthClient
from insights.sources.vtexcredentials.typing import VtexCredentialsDTO


class OrdersService:
    def __init__(self, project: Project) -> None:
        self.project = project

    def _get_credentials(self) -> VtexCredentialsDTO:
        """
        Get the credentials for the project
        """
        return VtexAuthClient(self.project.uuid).get_vtex_auth()

    def _get_internal_token(self):
        """
        Get the internal token for the project
        """
        return InternalAuthentication().get_module_token()

    def _get_client(self) -> VtexOrdersRestClient:
        """
        Get the client for the project
        """
        if self.project.vtex_account:
            return VtexOrdersRestClient(
                {
                    "domain": self.project.vtex_account,
                    "internal_token": self._get_internal_token(),
                },
                CacheClient(),
                use_io_proxy=True,
            )

        return VtexOrdersRestClient(self._get_credentials(), CacheClient())

    def _get_past_dates(self, start_date, end_date):
        period = (end_date - start_date).days

        past_start_date = start_date - timedelta(days=period)
        past_end_date = end_date - timedelta(days=period)

        return past_start_date, past_end_date

    def _calculate_increase_percentage(self, past_value, current_value):
        if past_value == 0:
            return 100 if current_value > 0 else 0

        return round(((current_value - past_value) / past_value) * 100, 2)

    def get_metrics_from_utm_source(self, utm_source, filters: dict) -> int:
        filters["utm_source"] = (utm_source,)

        start_date = filters.pop("start_date")
        end_date = filters.pop("end_date")

        filters["ended_at__gte"] = str(start_date)
        filters["ended_at__lte"] = str(end_date)

        # for the current period:
        data = self._get_client().list(filters)
        current_value = data.get("accumulatedTotal")
        current_orders_placed = data.get("countSell")
        currency_code = data.get("currencyCode")

        # for the past period:
        past_start_date, past_end_date = self._get_past_dates(start_date, end_date)

        filters["utm_source"] = (utm_source,)
        filters["ended_at__gte"] = str(past_start_date)
        filters["ended_at__lte"] = str(past_end_date)

        past_data = self._get_client().list(filters)
        past_value = past_data.get("accumulatedTotal")
        past_orders_placed = past_data.get("countSell")

        response = {
            "revenue": {
                "value": current_value,
                "currency_code": currency_code,
                "increase_percentage": self._calculate_increase_percentage(
                    past_value, current_value
                ),
            },
            "orders_placed": {
                "value": data.get("countSell"),
                "increase_percentage": self._calculate_increase_percentage(
                    past_orders_placed, current_orders_placed
                ),
            },
        }

        return response
