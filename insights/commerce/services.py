import json
import logging

from django.conf import settings
from rest_framework import status
from sentry_sdk import capture_exception

from insights.commerce.clients import BillingClient, RetailSetupClient
from insights.commerce.exceptions import (
    BillingRequestError,
    RetailSetupRequestError,
)
from insights.sources.cache import CacheClient

logger = logging.getLogger(__name__)


ABANDONED_CART_FEATURE_CODE = "abandoned_cart"
LEGACY_ABANDONED_CART_AGENT_SLUG = "active_cart_abandonment"

ABANDONED_CART_STATUS_CACHE_TTL = 60  # 1m
MARKETING_PRICING_CACHE_TTL = 300  # 5m


class AbandonedCartStatusService:
    """
    Service that determines whether the abandoned cart feature is active
    for a given project, by checking both the new integrated features
    model and the legacy agents model.
    """

    def __init__(self, client: RetailSetupClient | None = None):
        self.client = client or RetailSetupClient()
        self.cache = CacheClient()

    def is_active(self, project_uuid: str) -> bool:
        cache_key = f"commerce:abandoned_cart_status:{project_uuid}"

        if (cached := self.cache.get(cache_key)) is not None:
            return json.loads(cached)

        result = self._check_new_model(project_uuid) or self._check_legacy_model(
            project_uuid
        )

        self.cache.set(cache_key, json.dumps(result), ABANDONED_CART_STATUS_CACHE_TTL)

        return result

    def _check_new_model(self, project_uuid: str) -> bool:
        try:
            response = self.client.get_project_integrated_features(project_uuid)
        except RetailSetupRequestError as err:
            capture_exception(err)
            return False

        if not status.is_success(response.status_code):
            logger.warning(
                "Unexpected status %s from integrated features endpoint for project %s",
                response.status_code,
                project_uuid,
            )
            return False

        try:
            results = response.json().get("results", []) or []
        except ValueError:
            return False

        return any(
            item.get("code") == ABANDONED_CART_FEATURE_CODE for item in results
        )

    def _check_legacy_model(self, project_uuid: str) -> bool:
        try:
            response = self.client.get_project_agents(project_uuid)
        except RetailSetupRequestError as err:
            capture_exception(err)
            return False

        if not status.is_success(response.status_code):
            logger.warning(
                "Unexpected status %s from agents endpoint for project %s",
                response.status_code,
                project_uuid,
            )
            return False

        try:
            payload = response.json()
        except ValueError:
            return False

        gallery_agents = payload.get("gallery_agents", []) or []

        return any(
            agent.get("slug") == LEGACY_ABANDONED_CART_AGENT_SLUG
            and agent.get("assigned") is True
            for agent in gallery_agents
        )


class MarketingPricingService:
    """
    Service that returns the meta pricing rate for marketing messages
    of a given project.
    """

    def __init__(self, client: BillingClient | None = None):
        self.client = client or BillingClient()
        self.cache = CacheClient()

    def get_marketing_pricing(self, project_uuid: str) -> dict:
        if not getattr(settings, "BILLING_URL", ""):
            raise BillingRequestError("BILLING_URL is not configured")

        cache_key = f"commerce:marketing_pricing:{project_uuid}"

        if cached := self.cache.get(cache_key):
            return json.loads(cached)

        response = self.client.get_meta_pricing(project_uuid)

        if not status.is_success(response.status_code):
            raise BillingRequestError(
                f"Unexpected status {response.status_code} from billing service"
            )

        try:
            payload = response.json()
        except ValueError as err:
            raise BillingRequestError("Invalid JSON response from billing service") from err

        rates = payload.get("rates", {}) or {}
        raw_value = rates.get("marketing", 0)

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = 0.0

        data = {
            "value": value,
            "currency": payload.get("currency", "BRL"),
        }

        self.cache.set(cache_key, json.dumps(data), MARKETING_PRICING_CACHE_TTL)

        return data
