from functools import cached_property
import json
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
    TemplateNotFound,
)
from insights.metrics.skills.services.base import BaseSkillMetricsService
from insights.metrics.skills.validators import validate_date_str
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.sources.cache import CacheClient
from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.wabas.clients import WeniIntegrationsClient


ABANDONED_CART_METRICS_START_DATE_MAX_DAYS = 45


class AbandonedCartSkillService(BaseSkillMetricsService):
    def __init__(self, project, filters):
        super().__init__(project, filters)
        self.meta_api_client = MetaAPIClient()
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

        if valid_fields["start_date"] > valid_fields["end_date"]:
            raise InvalidDateRangeError("End date must be greater than start date")

        if valid_fields["start_date"] < (
            timezone.now().date()
            - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS)
        ):
            raise InvalidDateRangeError(
                f"Start date must be within the last {ABANDONED_CART_METRICS_START_DATE_MAX_DAYS} days"
            )

        if missing_fields:
            raise MissingFiltersError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        return valid_fields

    @cached_property
    def _project_wabas(self) -> list[dict]:
        client = WeniIntegrationsClient(self.project.uuid)
        wabas = client.get_wabas_for_project()

        return [waba for waba in wabas if waba["waba_id"]]

    @cached_property
    def _whatsapp_template_id_and_waba(self):
        name = "weni_abandoned_cart"

        template_id = None
        waba_id = None

        for waba in self._project_wabas:
            templates = self.meta_api_client.get_templates_list(waba_id=waba, name=name)

            if (
                len(templates.get("data", [])) > 0
                and templates["data"][0]["name"] == name
            ):
                template_id = templates["data"][0]["id"]
                waba_id = waba["waba_id"]
                break

        if not template_id or not waba_id:
            raise TemplateNotFound("No abandoned cart template found for the project")

        return template_id, waba_id

    def _calculate_increase_percentage(self, current: int, past: int):
        if past == 0:
            return 0

        return round(((current - past) / past) * 100, 2)

    def _get_message_templates_metrics(self, start_date, end_date) -> dict:
        template_id, waba_id = self._whatsapp_template_id_and_waba
        period = (end_date - start_date).days

        raw_start_date = start_date - timedelta(days=(period))
        raw_end_date = end_date

        metrics = self.meta_api_client.get_messages_analytics(
            waba_id=waba_id,
            template_id=template_id,
            start_date=raw_start_date,
            end_date=raw_end_date,
        )

        past_period_data_points = metrics.get("data", {}).get("data_points")[:period]
        current_period_data_points = metrics.get("data", {}).get("data_points")[period:]

        past_period_data = {
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "clicked": 0,
        }

        for day_data in past_period_data_points:
            past_period_data["sent"] += day_data["sent"]
            past_period_data["delivered"] += day_data["delivered"]
            past_period_data["read"] += day_data["read"]
            past_period_data["clicked"] += day_data["clicked"]

        current_period_data = {
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "clicked": 0,
        }

        for day_data in current_period_data_points:
            current_period_data["sent"] += day_data["sent"]
            current_period_data["delivered"] += day_data["delivered"]
            current_period_data["read"] += day_data["read"]
            current_period_data["clicked"] += day_data["clicked"]

        data = {
            "sent-messages": {
                "value": current_period_data["sent"],
                "percentage": self._calculate_increase_percentage(
                    current_period_data["sent"], past_period_data["sent"]
                ),
            },
            "delivered-messages": {
                "value": current_period_data["delivered"],
                "percentage": self._calculate_increase_percentage(
                    current_period_data["delivered"], past_period_data["delivered"]
                ),
            },
            "read-messages": {
                "value": current_period_data["read"],
                "percentage": self._calculate_increase_percentage(
                    current_period_data["read"], past_period_data["read"]
                ),
            },
            "interactions": {
                "value": current_period_data["clicked"],
                "percentage": self._calculate_increase_percentage(
                    current_period_data["clicked"], past_period_data["clicked"]
                ),
            },
        }

        return data

    def _get_orders_metrics(self, start_date, end_date) -> dict:
        utm_source = "weniabandonedcart"
        service = OrdersService(project_uuid=self.project.uuid)

        filters = {
            "start_date": start_date,
            "end_date": end_date,
        }

        return service.get_metrics_from_utm_source(
            utm_source=utm_source, filters=filters
        )

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

        data = [
            {
                "id": "sent-messages",
                "value": messages_metrics["sent-messages"]["value"],
                "percentage": messages_metrics["sent-messages"]["percentage"],
            },
            {
                "id": "delivered-messages",
                "value": messages_metrics["delivered-messages"]["value"],
                "percentage": messages_metrics["delivered-messages"]["percentage"],
            },
            {
                "id": "read-messages",
                "value": messages_metrics["read-messages"]["value"],
                "percentage": messages_metrics["read-messages"]["percentage"],
            },
            {
                "id": "interactions",
                "value": messages_metrics["interactions"]["value"],
                "percentage": messages_metrics["interactions"]["percentage"],
            },
            {
                "id": "utm-revenue",
                "value": orders_metrics.get("revenue", {}).get("value", 0),
                "percentage": orders_metrics.get("revenue", {}).get(
                    "increase_percentage", 0.0
                ),
                "prefix": "R$",  # TODO: Change
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
