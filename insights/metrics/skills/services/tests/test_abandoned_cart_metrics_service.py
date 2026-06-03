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
from insights.metrics.skills.services.dataclass import (
    AbandonedCartWabaTemplates,
    AbandonedCartWhatsAppTemplate,
)
from insights.dashboards.models import Dashboard
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
    def test_cannot_whatsapp_templates_by_waba_when_template_is_not_found(
        self, mock_templates_list
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "123456789098765"},
        )
        mock_templates_list.return_value = {"data": []}

        with self.assertRaises(TemplateNotFound):
            self.service_class(self.project, {})._whatsapp_templates_by_waba

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
    def test_whatsapp_templates_by_waba_returns_all_templates_sorted_desc(
        self, mock_templates_list
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_123"},
        )
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t2"},
                {"name": "weni_abandoned_cart_1700000050", "id": "t3"},
            ]
        }

        service = self.service_class(self.project, {})
        groups = service._whatsapp_templates_by_waba

        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group.waba_id, "waba_123")
        self.assertEqual(len(group.templates), 3)
        self.assertEqual(group.templates[0].name, "weni_abandoned_cart_1700000100")
        self.assertEqual(group.templates[0].ids, ["t2"])
        self.assertEqual(group.templates[1].name, "weni_abandoned_cart_1700000050")
        self.assertEqual(group.templates[1].ids, ["t3"])
        self.assertEqual(group.templates[2].name, "weni_abandoned_cart_1700000000")
        self.assertEqual(group.templates[2].ids, ["t1"])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_whatsapp_templates_by_waba_groups_ids_by_name(self, mock_templates_list):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_123"},
        )
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000000", "id": "t2"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t3"},
            ]
        }

        service = self.service_class(self.project, {})
        groups = service._whatsapp_templates_by_waba

        self.assertEqual(len(groups), 1)
        templates = groups[0].templates

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
                "data_points": [{"sent": 1, "delivered": 1, "read": 1, "clicked": 1}]
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
    def test_get_message_templates_metrics_combines_chunked_results(
        self, mock_templates_list, mock_analytics
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_123"},
        )
        mock_templates_list.return_value = {
            "data": [
                {"name": f"weni_abandoned_cart_{1700000000 + i}", "id": str(i)}
                for i in range(15)
            ]
        }

        mock_analytics.return_value = {
            "data": {
                "data_points": [{"sent": 10, "delivered": 8, "read": 5, "clicked": 2}]
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

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_whatsapp_templates_grouped_by_waba_when_project_has_multiple_wabas(
        self, mock_templates_list
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash_a",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_a"},
        )
        Dashboard.objects.create(
            project=self.project,
            name="dash_b",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_b"},
        )

        templates_by_waba = {
            "waba_a": {
                "data": [
                    {"name": "weni_abandoned_cart_1700000000", "id": "a1"},
                    {"name": "weni_abandoned_cart_1700000100", "id": "a2"},
                ]
            },
            "waba_b": {
                "data": [
                    {"name": "weni_abandoned_cart_1700000050", "id": "b1"},
                ]
            },
        }
        mock_templates_list.side_effect = lambda waba_id, name: templates_by_waba[
            waba_id
        ]

        service = self.service_class(self.project, {})
        groups = service._whatsapp_templates_by_waba

        self.assertEqual(len(groups), 2)
        self.assertIsInstance(groups[0], AbandonedCartWabaTemplates)

        groups_by_id = {group.waba_id: group for group in groups}

        group_a = groups_by_id["waba_a"]
        self.assertEqual(len(group_a.templates), 2)
        self.assertEqual(group_a.templates[0].name, "weni_abandoned_cart_1700000100")
        self.assertEqual(group_a.templates[0].ids, ["a2"])
        self.assertEqual(group_a.templates[1].name, "weni_abandoned_cart_1700000000")
        self.assertEqual(group_a.templates[1].ids, ["a1"])

        group_b = groups_by_id["waba_b"]
        self.assertEqual(len(group_b.templates), 1)
        self.assertEqual(group_b.templates[0].name, "weni_abandoned_cart_1700000050")
        self.assertEqual(group_b.templates[0].ids, ["b1"])

    @patch(
        "insights.metrics.skills.services.abandoned_cart.ABANDONED_CART_MAX_WABAS",
        2,
    )
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_whatsapp_templates_caps_at_max_wabas(self, mock_templates_list):
        for i in range(5):
            Dashboard.objects.create(
                project=self.project,
                name=f"dash_{i}",
                description="",
                config={"is_whatsapp_integration": True, "waba_id": f"waba_{i}"},
            )

        mock_templates_list.return_value = {
            "data": [{"name": "weni_abandoned_cart", "id": "t1"}]
        }

        service = self.service_class(self.project, {})
        groups = service._whatsapp_templates_by_waba

        self.assertEqual(mock_templates_list.call_count, 2)
        self.assertEqual(len(groups), 2)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_get_message_templates_metrics_calls_analytics_per_waba_and_product_type(
        self, mock_templates_list, mock_analytics
    ):
        Dashboard.objects.create(
            project=self.project,
            name="dash_a",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_a"},
        )
        Dashboard.objects.create(
            project=self.project,
            name="dash_b",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_b"},
        )

        templates_by_waba = {
            "waba_a": {
                "data": [
                    {"name": "weni_abandoned_cart_a", "id": "a1"},
                    {"name": "weni_abandoned_cart_a", "id": "a2"},
                ]
            },
            "waba_b": {
                "data": [
                    {"name": "weni_abandoned_cart_b", "id": "b1"},
                ]
            },
        }
        mock_templates_list.side_effect = lambda waba_id, name: templates_by_waba[
            waba_id
        ]

        mock_analytics.return_value = {
            "data": {
                "data_points": [{"sent": 10, "delivered": 8, "read": 5, "clicked": 2}]
            }
        }

        service = self.service_class(self.project, {})
        result = service._get_message_templates_metrics("2024-01-01", "2024-01-31")

        # 2 WABAs x 2 product types = 4 calls (each WABA fits in a single chunk).
        self.assertEqual(mock_analytics.call_count, 4)

        calls_by_waba = {"waba_a": [], "waba_b": []}
        for call in mock_analytics.call_args_list:
            kwargs = call.kwargs
            calls_by_waba[kwargs["waba_id"]].append(kwargs)

        self.assertEqual(len(calls_by_waba["waba_a"]), 2)
        self.assertEqual(len(calls_by_waba["waba_b"]), 2)

        for kwargs in calls_by_waba["waba_a"]:
            self.assertCountEqual(kwargs["template_id"], ["a1", "a2"])
        for kwargs in calls_by_waba["waba_b"]:
            self.assertEqual(kwargs["template_id"], ["b1"])

        product_types_a = {kwargs["product_type"] for kwargs in calls_by_waba["waba_a"]}
        product_types_b = {kwargs["product_type"] for kwargs in calls_by_waba["waba_b"]}
        expected_product_types = {
            ProductType.CLOUD_API.value,
            ProductType.MM_LITE.value,
        }
        self.assertEqual(product_types_a, expected_product_types)
        self.assertEqual(product_types_b, expected_product_types)

        self.assertEqual(result["sent-messages"]["value"], 40)
        self.assertEqual(result["delivered-messages"]["value"], 32)
        self.assertEqual(result["read-messages"]["value"], 20)
        self.assertEqual(result["interactions"]["value"], 8)
