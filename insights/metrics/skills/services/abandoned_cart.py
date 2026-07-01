import json
import logging

from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.skills.exceptions import (
    ErrorGettingOrdersMetrics,
    InvalidDateRangeError,
    MissingFiltersError,
    TemplateNotFound,
)
from insights.metrics.skills.services.base import BaseSkillMetricsService
from insights.metrics.skills.usecases.format_abandoned_cart_skill_response import (
    FormatAbandonedCartSkillResponse,
)
from insights.metrics.skills.validators import validate_date_str
from insights.metrics.templates_and_orders.exceptions import (
    ErrorGettingOrdersMetrics as TemplatesOrdersErrorGettingOrdersMetrics,
    TemplatesNotFoundError,
)
from insights.metrics.templates_and_orders.usecases.get_templates_and_orders_metrics import (
    GetTemplatesAndOrdersMetrics,
    MetricsLimits,
)
from insights.settings import (
    ABANDONED_CART_MAX_TEMPLATE_IDS,
    ABANDONED_CART_MAX_WABAS,
    ABANDONED_CART_METRICS_START_DATE_MAX_DAYS,
)
from insights.sources.cache import CacheClient

logger = logging.getLogger(__name__)


class AbandonedCartSkillService(BaseSkillMetricsService):
    UTM_SOURCE = "weniabandonedcart"
    TEMPLATE_PREFIX = "weni_abandoned_cart"

    def __init__(
        self,
        project,
        filters,
        get_templates_and_orders_metrics: GetTemplatesAndOrdersMetrics | None = None,
        format_response: FormatAbandonedCartSkillResponse | None = None,
    ):
        super().__init__(project, filters)
        self.get_templates_and_orders_metrics = (
            get_templates_and_orders_metrics or GetTemplatesAndOrdersMetrics()
        )
        self.format_response = format_response or FormatAbandonedCartSkillResponse()
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

    def get_metrics(self):
        filters = self.validate_filters(self.filters)

        cache_key = f"metrics_abandoned_cart_{self.project.uuid}:{json.dumps(filters, sort_keys=True, default=str)}"

        if cached_data := self.cache_client.get(cache_key):
            return json.loads(cached_data)

        try:
            raw_metrics = self.get_templates_and_orders_metrics.execute(
                project=self.project,
                start_date=filters["start_date"],
                end_date=filters["end_date"],
                utm_source=self.UTM_SOURCE,
                template_name_prefix=self.TEMPLATE_PREFIX,
                limits=MetricsLimits(
                    max_wabas=ABANDONED_CART_MAX_WABAS,
                    max_template_ids=ABANDONED_CART_MAX_TEMPLATE_IDS,
                ),
                require_templates=True,
            )
        except TemplatesNotFoundError as error:
            raise TemplateNotFound(
                "No abandoned cart template found for the project"
            ) from error
        except TemplatesOrdersErrorGettingOrdersMetrics as error:
            raise ErrorGettingOrdersMetrics(str(error)) from error

        data = self.format_response.execute(raw_metrics)

        self.cache_client.set(cache_key, json.dumps(data, default=str), self.cache_ttl)

        return data
