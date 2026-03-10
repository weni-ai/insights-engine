from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.metrics.meta.tests.mock import MOCK_TEMPLATE_DAILY_ANALYTICS
from insights.metrics.meta.utils import format_messages_metrics_data
from insights.projects.models import Project
from insights.sources.vtex_conversions.services import VTEXOrdersConversionsService
from rest_framework.exceptions import PermissionDenied


class VTEXConversionsServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.project = Project.objects.create(timezone="America/Sao_Paulo")

        self.meta_api_client = Mock()
        self.integrations_client = Mock()
        self.orders_client = Mock()

        self.service = VTEXOrdersConversionsService(
            self.project,
            self.meta_api_client,
            self.integrations_client,
            self.orders_client,
        )

    def test_cannot_get_metrics_without_required_filters(self):
        filters = {}

        with self.assertRaises(serializers.ValidationError) as context:
            self.service.get_metrics(filters)

        for field in ("waba_id", "template_id", "ended_at__gte", "ended_at__lte"):
            self.assertIn(field, context.exception.detail)
            self.assertEqual(context.exception.detail[field][0].code, "required")

    def test_cannot_get_metrics_without_waba_permission(self):
        self.integrations_client.get_wabas_for_project.return_value = []

        filters = {
            "waba_id": "123",
            "template_id": "456",
            "utm_source": "example",
            "ended_at__gte": (timezone.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "ended_at__lte": (timezone.now()).strftime("%Y-%m-%d"),
        }

        with self.assertRaises(PermissionDenied) as context:
            self.service.get_metrics(filters)

        self.assertEqual(
            context.exception.detail.code, "project_without_waba_permission"
        )

    def test_get_metrics(self):
        waba_id = "123"

        analytics_mock_data = MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
        formatted_analytics_mock_data = format_messages_metrics_data(
            analytics_mock_data
        )

        self.integrations_client.get_wabas_for_project.return_value = [
            {"waba_id": waba_id}
        ]
        self.meta_api_client.get_messages_analytics.return_value = {
            "data": formatted_analytics_mock_data
        }

        fake_utm_data = {
            "count_sell": 10,
            "accumulated_total": 10000,
            "medium_ticket": 1000,
            "currency_code": "BRL",
        }

        self.orders_client.list.return_value = {
            "countSell": fake_utm_data.get("count_sell"),
            "accumulatedTotal": fake_utm_data.get("accumulated_total"),
            "ticketMax": 1000,
            "ticketMin": 100,
            "medium_ticket": fake_utm_data.get("medium_ticket"),
            "currencyCode": fake_utm_data.get("currency_code"),
        }
        self.meta_api_client.get_messages_analytics.return_value = {
            "data": formatted_analytics_mock_data
        }

        filters = {
            "waba_id": waba_id,
            "template_id": "456",
            "utm_source": "example",
            "ended_at__gte": (timezone.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "ended_at__lte": (timezone.now()).strftime("%Y-%m-%d"),
        }

        Dashboard.objects.create(
            project=self.project,
            config={"is_whatsapp_integration": True, "waba_id": waba_id},
        )

        metrics = self.service.get_metrics(filters)

        self.assertIn("utm_data", metrics)

        for key, value in fake_utm_data.items():
            self.assertIn(key, metrics["utm_data"])
            self.assertEqual(metrics["utm_data"][key], value)

        for status in ("sent", "delivered", "read", "clicked"):
            self.assertIn(status, metrics["graph_data"])
            self.assertIn("value", metrics["graph_data"][status])
            self.assertEqual(
                metrics["graph_data"][status]["value"],
                formatted_analytics_mock_data.get("status_count")
                .get(status)
                .get("value"),
            )

            if status != "sent":
                self.assertIn("percentage", metrics["graph_data"][status])
                self.assertEqual(
                    metrics["graph_data"][status]["percentage"],
                    formatted_analytics_mock_data.get("status_count")
                    .get(status)
                    .get("percentage"),
                )

        self.assertIn("orders", metrics["graph_data"])
        self.assertIn("value", metrics["graph_data"]["orders"])
        self.assertIn("percentage", metrics["graph_data"]["orders"])
        self.assertEqual(
            metrics["graph_data"]["orders"]["value"], fake_utm_data.get("count_sell")
        )
        self.assertEqual(
            metrics["graph_data"]["orders"]["percentage"],
            round(
                (
                    fake_utm_data.get("count_sell")
                    / formatted_analytics_mock_data.get("status_count")
                    .get("sent")
                    .get("value")
                )
                * 100,
                2,
            ),
        )
