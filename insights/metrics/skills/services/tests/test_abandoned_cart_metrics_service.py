import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
    TemplateNotFound,
)
from insights.metrics.meta.enums import ProductType
from insights.metrics.skills.services.abandoned_cart import (
    ABANDONED_CART_METRICS_START_DATE_MAX_DAYS,
    AbandonedCartSkillService,
)
from insights.metrics.skills.services.dataclass import AbandonedCartWhatsAppTemplate
from insights.projects.models import Project
from insights.sources.cache import CacheClient
from insights.metrics.meta.utils import (
    format_messages_metrics_data,
)


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

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_whatsapp_template_id_and_waba_when_template_is_not_found(
        self, mock_wabas, mock_templates_list
    ):
        mock_wabas.return_value = [
            {
                "waba_id": "123456789098765",
            },
        ]
        mock_templates_list.return_value = {"data": []}

        with self.assertRaises(TemplateNotFound):
            self.service_class(self.project, {})._whatsapp_template_ids_and_waba

    @patch("insights.sources.orders.clients.VtexOrdersRestClient.list")
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_get_metrics(
        self,
        mock_wabas,
        mock_templates_list,
        mock_messages_analytics,
        mock_get_vtex_auth,
        mock_vtex_orders_list,
    ):
        mock_wabas.return_value = [
            {
                "waba_id": "123456789098765",
            },
        ]
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

        # The numbers are doubled because we are using both Cloud API and MM Lite.
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
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_whatsapp_template_ids_returns_all_templates_sorted_desc(
        self, mock_wabas, mock_templates_list
    ):
        mock_wabas.return_value = [{"waba_id": "waba_123"}]
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t2"},
                {"name": "weni_abandoned_cart_1700000050", "id": "t3"},
            ]
        }

        service = self.service_class(self.project, {})
        templates, waba_id = service._whatsapp_template_ids_and_waba

        self.assertEqual(waba_id, "waba_123")
        self.assertEqual(len(templates), 3)
        self.assertEqual(templates[0].name, "weni_abandoned_cart_1700000100")
        self.assertEqual(templates[0].ids, ["t2"])
        self.assertEqual(templates[1].name, "weni_abandoned_cart_1700000050")
        self.assertEqual(templates[1].ids, ["t3"])
        self.assertEqual(templates[2].name, "weni_abandoned_cart_1700000000")
        self.assertEqual(templates[2].ids, ["t1"])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_whatsapp_template_ids_groups_ids_by_name(
        self, mock_wabas, mock_templates_list
    ):
        mock_wabas.return_value = [{"waba_id": "waba_123"}]
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000000", "id": "t2"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t3"},
            ]
        }

        service = self.service_class(self.project, {})
        templates, waba_id = service._whatsapp_template_ids_and_waba

        self.assertEqual(len(templates), 2)
        self.assertEqual(templates[0].name, "weni_abandoned_cart_1700000100")
        self.assertEqual(templates[0].ids, ["t3"])
        self.assertEqual(templates[1].name, "weni_abandoned_cart_1700000000")
        self.assertCountEqual(templates[1].ids, ["t1", "t2"])

    def test_get_capped_template_ids_returns_all_when_under_limit(self):
        templates = [
            AbandonedCartWhatsAppTemplate(name="tpl_b", ids=["1", "2", "3"]),
            AbandonedCartWhatsAppTemplate(name="tpl_a", ids=["4", "5"]),
        ]
        service = self.service_class(self.project, {})
        result = service._get_capped_template_ids(templates)

        self.assertEqual(result, ["1", "2", "3", "4", "5"])

    @patch(
        "insights.metrics.skills.services.abandoned_cart.ABANDONED_CART_MAX_TEMPLATE_IDS",
        5,
    )
    def test_get_capped_template_ids_caps_at_max(self):
        templates = [
            AbandonedCartWhatsAppTemplate(name="tpl_c", ids=["1", "2", "3"]),
            AbandonedCartWhatsAppTemplate(name="tpl_b", ids=["4", "5", "6", "7"]),
            AbandonedCartWhatsAppTemplate(name="tpl_a", ids=["8", "9"]),
        ]
        service = self.service_class(self.project, {})
        result = service._get_capped_template_ids(templates)

        self.assertEqual(len(result), 5)
        self.assertEqual(result, ["1", "2", "3", "4", "5"])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_fetch_analytics_chunks_requests(self, mock_analytics):
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 1, "delivered": 1, "read": 1, "clicked": 1}
                ]
            }
        }

        service = self.service_class(self.project, {})
        template_ids = [str(i) for i in range(25)]

        result = service._fetch_analytics_for_template_ids(
            waba_id="waba_123",
            template_ids=template_ids,
            start_date="2024-01-01",
            end_date="2024-01-31",
            product_type=ProductType.CLOUD_API.value,
        )

        self.assertEqual(mock_analytics.call_count, 3)
        self.assertEqual(len(result), 3)

        first_call_ids = mock_analytics.call_args_list[0].kwargs["template_id"]
        second_call_ids = mock_analytics.call_args_list[1].kwargs["template_id"]
        third_call_ids = mock_analytics.call_args_list[2].kwargs["template_id"]
        self.assertEqual(len(first_call_ids), 10)
        self.assertEqual(len(second_call_ids), 10)
        self.assertEqual(len(third_call_ids), 5)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_get_message_templates_metrics_combines_chunked_results(
        self, mock_wabas, mock_templates_list, mock_analytics
    ):
        mock_wabas.return_value = [{"waba_id": "waba_123"}]
        mock_templates_list.return_value = {
            "data": [
                {"name": f"weni_abandoned_cart_{1700000000 + i}", "id": str(i)}
                for i in range(15)
            ]
        }

        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 10, "delivered": 8, "read": 5, "clicked": 2}
                ]
            }
        }

        service = self.service_class(self.project, {})
        result = service._get_message_templates_metrics("2024-01-01", "2024-01-31")

        # 15 IDs -> 2 chunks per product type -> 4 calls total
        self.assertEqual(mock_analytics.call_count, 4)
        self.assertEqual(result["sent-messages"]["value"], 40)
        self.assertEqual(result["delivered-messages"]["value"], 32)
        self.assertEqual(result["read-messages"]["value"], 20)
        self.assertEqual(result["interactions"]["value"], 8)
