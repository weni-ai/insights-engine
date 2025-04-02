from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import serializers

from insights.metrics.meta.tests.mock import MOCK_TEMPLATE_DAILY_ANALYTICS
from insights.metrics.meta.utils import format_messages_metrics_data
from insights.metrics.meta.validators import MAX_ANALYTICS_DAYS_PERIOD_FILTER
from insights.projects.models import Project
from insights.sources.vtex_conversions.services import VTEXOrdersConversionsService
from rest_framework.exceptions import PermissionDenied

from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class VTEXConversionsServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.project = Project.objects.create()
        self.service = VTEXOrdersConversionsService(self.project)

    def test_cannot_get_metrics_without_required_filters(self):
        filters = {}

        with self.assertRaises(serializers.ValidationError) as context:
            self.service.get_metrics(filters)

        for field in ("waba_id", "template_id", "ended_at__gte", "ended_at__lte"):
            self.assertIn(field, context.exception.detail)
            self.assertEqual(context.exception.detail[field][0].code, "required")

    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_metrics_without_waba_permission(
        self, mock_get_wabas_for_project
    ):
        mock_get_wabas_for_project.return_value = []

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

    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    def test_cannot_get_metrics_without_vtex_credentials(
        self, mock_get_vtex_auth, mock_get_wabas_for_project
    ):
        waba_id = "123"
        mock_get_vtex_auth.side_effect = VtexCredentialsNotFound()
        mock_get_wabas_for_project.return_value = [waba_id]

        filters = {
            "waba_id": waba_id,
            "template_id": "456",
            "utm_source": "example",
            "ended_at__gte": (timezone.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "ended_at__lte": (timezone.now()).strftime("%Y-%m-%d"),
        }

        with self.assertRaises(PermissionDenied) as context:
            self.service.get_metrics(filters)

        self.assertEqual(
            context.exception.detail.code, "project_without_vtex_credentials"
        )

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    @patch("insights.sources.orders.clients.VtexOrdersRestClient.list")
    def test_get_metrics(
        self,
        mock_get_vtex_orders,
        mock_get_vtex_auth,
        mock_get_wabas_for_project,
        mock_get_messages_analytics,
    ):
        waba_id = "123"

        analytics_mock_data = MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
        formatted_analytics_mock_data = format_messages_metrics_data(
            analytics_mock_data
        )

        mock_get_wabas_for_project.return_value = [waba_id]
        mock_get_vtex_auth.return_value = {
            "app_key": "123",
            "app_token": "123",
            "domain": "example.myvtex.com",
        }

        fake_utm_data = {
            "count_sell": 10,
            "accumulated_total": 10000,
            "medium_ticket": 1000,
            "currency_code": "BRL",
        }

        mock_get_vtex_orders.return_value = {
            "countSell": fake_utm_data.get("count_sell"),
            "accumulatedTotal": fake_utm_data.get("accumulated_total"),
            "ticketMax": 1000,
            "ticketMin": 100,
            "medium_ticket": fake_utm_data.get("medium_ticket"),
            "currencyCode": fake_utm_data.get("currency_code"),
        }
        mock_get_messages_analytics.return_value = {
            "data": formatted_analytics_mock_data
        }

        filters = {
            "waba_id": waba_id,
            "template_id": "456",
            "utm_source": "example",
            "ended_at__gte": (timezone.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "ended_at__lte": (timezone.now()).strftime("%Y-%m-%d"),
        }

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
