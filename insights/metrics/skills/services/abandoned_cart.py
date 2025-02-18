from functools import cached_property
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
)
from insights.metrics.skills.services.base import BaseSkillMetricsService
from insights.metrics.skills.validators import validate_date_str
from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.wabas.clients import WeniIntegrationsClient


ABANDONED_CART_METRICS_START_DATE_MAX_DAYS = 45


class AbandonedCartSkillService(BaseSkillMetricsService):
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

        return client.get_wabas_for_project()

    @cached_property
    def _whatsapp_template_id(self):
        client = MetaAPIClient()

        for waba in self._project_wabas:
            # TODO: get list in Meta API
            pass

        return None

    def _get_message_templates_metrics(self, start_date, end_date) -> dict:
        client = MetaAPIClient()
        # TODO

    def get_metrics(self):
        filters = self.validate_filters(self.filters)
        period = (filters["end_date"] - filters["start_date"]).days()

        return {}
