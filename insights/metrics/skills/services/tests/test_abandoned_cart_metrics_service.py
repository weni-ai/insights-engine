import json
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.dashboards.models import Dashboard
from insights.metrics.meta.utils import format_messages_metrics_data
from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
    TemplateNotFound,
)
from insights.metrics.skills.services.abandoned_cart import (
    ABANDONED_CART_METRICS_START_DATE_MAX_DAYS,
    AbandonedCartSkillService,
)
from insights.metrics.skills.usecases.format_abandoned_cart_skill_response import (
    FormatAbandonedCartSkillResponse,
)
from insights.metrics.templates_and_orders.usecases.get_templates_and_orders_metrics import (
    GetTemplatesAndOrdersMetrics,
    MetricsLimits,
)
from insights.projects.models import Project
from insights.settings import (
    ABANDONED_CART_MAX_TEMPLATE_IDS,
    ABANDONED_CART_MAX_WABAS,
)
from insights.sources.cache import CacheClient


class TestAbandonedCartSkillService(TestCase):
    def setUp(self):
        self.service_class = AbandonedCartSkillService
        self.project = Project.objects.create()
        self.cache_client = CacheClient()

        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_missing_filters_on_validation(self):
        filters = {}
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            MissingFiltersError, "Missing required fields: start_date, end_date"
        ):
            service.validate_filters(filters)

    def test_validate_filters_with_start_date_greater_than_end_date(self):
        filters = {
            "start_date": (timezone.now()).date().isoformat(),
            "end_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
        }
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            InvalidDateRangeError, "End date must be greater than start date"
        ):
            service.validate_filters(filters)

    def test_validate_filters_with_invalid_start_date(self):
        filters = {
            "start_date": (
                timezone.now()
                - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS + 1)
            )
            .date()
            .isoformat(),
            "end_date": (
                timezone.now()
                - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS - 10)
            )
            .date()
            .isoformat(),
        }
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            InvalidDateRangeError,
            f"Start date must be within the last {ABANDONED_CART_METRICS_START_DATE_MAX_DAYS} days",
        ):
            service.validate_filters(filters)

    @patch("insights.sources.orders.clients.VtexOrdersRestClient.list")
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_get_metrics(
        self,
        mock_templates_list,
        mock_messages_analytics,
        mock_get_vtex_auth,
        mock_vtex_orders_list,
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "123456789098765"},
        )
        mock_templates_list.return_value = {
            "data": [
                {
                    "name": "weni_abandoned_cart",
                    "id": "123456789098765",
                },
            ]
        }

        data_points_for_period = [
            {
                "template_id": "123456789098765",
                "start": 1733011200,
                "end": 1733097600,
                "sent": 10,
                "delivered": 9,
                "read": 8,
                "clicked": [
                    {
                        "type": "quick_reply_button",
                        "button_content": "Access service",
                        "count": 7,
                    },
                ],
            }
            for _ in range(5)
        ]

        data_points = data_points_for_period
        mock_messages_analytics.return_value = {
            "data": format_messages_metrics_data({"data_points": data_points}),
        }

        mock_get_vtex_auth.return_value = {
            "app_token": "fake_token",
            "app_key": "fake_key",
            "domain": "fake_domain",
        }

        expected_count = 2
        expected_utm_revenue = 50.21

        mock_vtex_orders_list.return_value = {
            "countSell": expected_count,
            "accumulatedTotal": expected_utm_revenue,
            "ticketMax": 50.21,
            "ticketMin": 50.21,
            "medium_ticket": 50.21,
            "currencyCode": "BRL",
        }

        filters = {
            "start_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
            "end_date": (timezone.now()).date().isoformat(),
        }
        service = self.service_class(self.project, filters)

        cache_key = f"metrics_abandoned_cart_{self.project.uuid}:{json.dumps(filters, sort_keys=True, default=str)}"
        self.assertIsNone(self.cache_client.get(cache_key))

        metrics = service.get_metrics()

        expected_metrics = [
            {
                "id": "sent-messages",
                "value": 100,
            },
            {
                "id": "delivered-messages",
                "value": 90,
            },
            {
                "id": "read-messages",
                "value": 80,
            },
            {
                "id": "interactions",
                "value": 70,
            },
            {
                "id": "utm-revenue",
                "value": expected_utm_revenue,
                "percentage": 0,
                "prefix": "R$",
            },
            {
                "id": "orders-placed",
                "value": expected_count,
                "percentage": 0,
            },
        ]

        self.assertEqual(metrics, expected_metrics)
        self.assertEqual(json.loads(self.cache_client.get(cache_key)), expected_metrics)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_get_metrics_raises_template_not_found_when_no_templates(
        self, mock_templates_list
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "123456789098765"},
        )
        mock_templates_list.return_value = {"data": []}

        filters = {
            "start_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
            "end_date": (timezone.now()).date().isoformat(),
        }
        service = self.service_class(self.project, filters)

        with self.assertRaises(TemplateNotFound):
            service.get_metrics()

    def test_get_metrics_delegates_to_shared_usecase_with_abandoned_cart_params(self):
        mock_get_metrics = MagicMock(spec=GetTemplatesAndOrdersMetrics)
        mock_format_response = MagicMock(spec=FormatAbandonedCartSkillResponse)

        raw_metrics = {
            "template_metrics": {
                "sent": 10,
                "delivered": 8,
                "read": 5,
                "clicked": 2,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 100,
                    "currency_code": "BRL",
                    "increase_percentage": 0,
                },
                "orders_placed": {"value": 3, "increase_percentage": 0},
            },
        }
        formatted_metrics = [{"id": "sent-messages", "value": 10}]

        mock_get_metrics.execute.return_value = raw_metrics
        mock_format_response.execute.return_value = formatted_metrics

        filters = {
            "start_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
            "end_date": (timezone.now()).date().isoformat(),
        }
        service = self.service_class(
            self.project,
            filters,
            get_templates_and_orders_metrics=mock_get_metrics,
            format_response=mock_format_response,
        )
        validated_filters = service.validate_filters(filters)

        result = service.get_metrics()

        mock_get_metrics.execute.assert_called_once_with(
            project=self.project,
            start_date=validated_filters["start_date"],
            end_date=validated_filters["end_date"],
            utm_source=AbandonedCartSkillService.UTM_SOURCE,
            template_name_prefix=AbandonedCartSkillService.TEMPLATE_PREFIX,
            limits=MetricsLimits(
                max_wabas=ABANDONED_CART_MAX_WABAS,
                max_template_ids=ABANDONED_CART_MAX_TEMPLATE_IDS,
            ),
            require_templates=True,
        )
        mock_format_response.execute.assert_called_once_with(raw_metrics)
        self.assertEqual(result, formatted_metrics)
