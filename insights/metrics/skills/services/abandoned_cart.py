from functools import cached_property
import json
import logging

from babel import numbers
from django.utils import timezone
from django.utils.timezone import timedelta
from sentry_sdk import capture_exception

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.skills.exceptions import (
    ErrorGettingOrdersMetrics,
    InvalidDateRangeError,
    MissingFiltersError,
    TemplateNotFound,
)
from insights.metrics.skills.services.base import BaseSkillMetricsService
from insights.metrics.skills.validators import validate_date_str
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.sources.cache import CacheClient
from insights.sources.integrations.clients import WeniIntegrationsClient


ABANDONED_CART_METRICS_START_DATE_MAX_DAYS = 90

logger = logging.getLogger(__name__)


class AbandonedCartSkillService(BaseSkillMetricsService):
    def __init__(self, project, filters):
        super().__init__(project, filters)
        self.meta_api_client = MetaGraphAPIClient()
        self.cache_client = CacheClient()
        self.cache_ttl = 3600  # 1h

    def validate_filters(self, filters: dict):
        required_fields = ["start_date", "end_date"]
        missing_fields = []
        valid_fields = {}

        for field in required_fields:
            if field not in filters:
                missing_fields.append(field)
            else:
                valid_fields[field] = validate_date_str(filters[field])

        if missing_fields:
            raise MissingFiltersError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        if valid_fields["start_date"] > valid_fields["end_date"]:
            raise InvalidDateRangeError("End date must be greater than start date")

        if valid_fields["start_date"] <= (
            timezone.now().date()
            - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS)
        ):
            raise InvalidDateRangeError(
                f"Start date must be within the last {ABANDONED_CART_METRICS_START_DATE_MAX_DAYS} days"
            )

        return valid_fields

    @cached_property
    def _project_wabas(self) -> list[dict]:
        client = WeniIntegrationsClient()
        try:
            wabas = client.get_wabas_for_project(self.project.uuid)
        except ValueError as e:
            logger.error(
                "Error fetching wabas in AbandonedCartSkillService for project %s: %s",
                self.project.uuid,
                e,
            )

            raise e

        return [waba for waba in wabas if waba["waba_id"]]

    @cached_property
    def _whatsapp_template_ids_and_waba(self):
        name = "weni_abandoned_cart"

        template_ids = []
        waba_id = None

        most_recent_template_name = ""

        for waba in self._project_wabas:
            templates = self.meta_api_client.get_templates_list(
                waba_id=waba["waba_id"], name=name
            )

            if len(templates.get("data", [])) == 0:
                continue

            for template in templates.get("data", []):
                if template["name"] >= most_recent_template_name:
                    if template["name"] == most_recent_template_name:
                        template_ids.append(template["id"])
                    else:
                        template_ids = [template["id"]]

                    most_recent_template_name = template["name"]
                    waba_id = waba["waba_id"]

        if not template_ids or not waba_id:
            raise TemplateNotFound("No abandoned cart template found for the project")

        return template_ids, waba_id

    def _calculate_increase_percentage(self, current: int, past: int):
        if past == 0:
            return 100 if current > 0 else 0

        return round(((current - past) / past) * 100, 2)

    def _get_message_templates_metrics(self, start_date, end_date) -> dict:
        template_ids, waba_id = self._whatsapp_template_ids_and_waba

        metrics = self.meta_api_client.get_messages_analytics(
            waba_id=waba_id,
            template_id=template_ids,
            start_date=start_date,
            end_date=end_date,
        )

        data_points = metrics.get("data", {}).get("data_points")

        period_data = {
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "clicked": 0,
        }

        for day_data in data_points:
            period_data["sent"] += day_data["sent"]
            period_data["delivered"] += day_data["delivered"]
            period_data["read"] += day_data["read"]
            period_data["clicked"] += day_data["clicked"]

        data = {
            "sent-messages": {"value": period_data["sent"]},
            "delivered-messages": {"value": period_data["delivered"]},
            "read-messages": {"value": period_data["read"]},
            "interactions": {"value": period_data["clicked"]},
        }

        return data

    def _get_orders_metrics(self, start_date, end_date) -> dict:
        utm_source = "weniabandonedcart"
        service = OrdersService(self.project)

        filters = {
            "start_date": start_date,
            "end_date": end_date,
        }

        try:
            return service.get_metrics_from_utm_source(
                utm_source=utm_source, filters=filters
            )
        except Exception as e:
            capture_exception(e)
            logger.error("Error getting orders from VTEX: %s", e, exc_info=True)

            raise ErrorGettingOrdersMetrics("Error getting orders from VTEX") from e

    def get_metrics(self):
        filters = self.validate_filters(self.filters)

        cache_key = f"metrics_abandoned_cart_{self.project.uuid}:{json.dumps(filters, sort_keys=True, default=str)}"

        if cached_data := self.cache_client.get(cache_key):
            return json.loads(cached_data)

        messages_metrics = self._get_message_templates_metrics(
            start_date=filters.get("start_date"), end_date=filters.get("end_date")
        )
        orders_metrics = self._get_orders_metrics(
            start_date=filters.get("start_date"), end_date=filters.get("end_date")
        )

        currency_symbol = ""

        if currency_code := orders_metrics.get("revenue", {}).get("currency_code"):
            currency_symbol = numbers.get_currency_symbol(currency_code)

        data = [
            {
                "id": "sent-messages",
                "value": messages_metrics["sent-messages"]["value"],
            },
            {
                "id": "delivered-messages",
                "value": messages_metrics["delivered-messages"]["value"],
            },
            {
                "id": "read-messages",
                "value": messages_metrics["read-messages"]["value"],
            },
            {
                "id": "interactions",
                "value": messages_metrics["interactions"]["value"],
            },
            {
                "id": "utm-revenue",
                "value": orders_metrics.get("revenue", {}).get("value", 0),
                "percentage": orders_metrics.get("revenue", {}).get(
                    "increase_percentage", 0.0
                ),
                "prefix": currency_symbol,
            },
            {
                "id": "orders-placed",
                "value": orders_metrics.get("orders_placed", {}).get("value", 0),
                "percentage": orders_metrics.get("orders_placed", {}).get(
                    "increase_percentage", 0.0
                ),
            },
        ]

        self.cache_client.set(cache_key, json.dumps(data, default=str), self.cache_ttl)

        return data
