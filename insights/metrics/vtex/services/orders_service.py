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

    def _get_utm_source_from_feature(self, feature: str) -> str:
        features = {"abandoned_cart": "weniabandonedcart"}

        utm_source = features.get(feature)

        if not utm_source:
            raise ValidationError(
                {"feature": [_("Invalid feature")]}, code="invalid_feature"
            )

        return utm_source

    def get_utm_revenue(self, feature, filters: dict) -> int:
        filters["utm_source"] = self._get_utm_source_from_feature(feature)

        data = self._get_client().list(filters)
        value = data.get("accumulatedTotal")

        return value
