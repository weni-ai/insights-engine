from unittest.mock import patch
from django.test import TestCase
from rest_framework import serializers
from insights.metrics.meta.tests.mock import MOCK_TEMPLATE_DAILY_ANALYTICS
from insights.metrics.meta.utils import format_messages_metrics_data
from insights.projects.models import Project
from insights.sources.vtex_conversions.services import VTEXOrdersConversionsService
from rest_framework.exceptions import PermissionDenied


class VTEXConversionsServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.project = Project.objects.create()
        self.service = VTEXOrdersConversionsService(self.project)

    def test_cannot_get_metrics_without_required_filters(self):
        filters = {}

        with self.assertRaises(serializers.ValidationError) as context:
            self.service.get_metrics(filters)

        for field in ("waba_id", "template_id", "date_start", "date_end"):
            self.assertIn(field, context.exception.detail)
            self.assertEqual(context.exception.detail[field][0].code, "required")

    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_cannot_get_metrics_without_permission(self, mock_get_wabas_for_project):
        mock_get_wabas_for_project.return_value = []

        filters = {
            "waba_id": "123",
            "template_id": "456",
            "date_start": "2021-01-01",
            "date_end": "2021-01-01",
        }

        with self.assertRaises(PermissionDenied):
            self.service.get_metrics(filters)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    @patch(
        "insights.sources.integrations.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_get_metrics(self, mock_get_wabas_for_project, mock_get_messages_analytics):
        waba_id = "123"

        analytics_mock_data = MOCK_TEMPLATE_DAILY_ANALYTICS.get("data")[0]
        formatted_analytics_mock_data = format_messages_metrics_data(
            analytics_mock_data
        )

        mock_get_wabas_for_project.return_value = ["123"]
        mock_get_messages_analytics.return_value = {
            "data": formatted_analytics_mock_data
        }

        filters = {
            "waba_id": waba_id,
            "template_id": "456",
            "date_start": "2025-01-24",
            "date_end": "2025-01-31",
        }

        metrics = self.service.get_metrics(filters)

        self.assertIn("graph_data", metrics)
        self.assertIn("sent", metrics["graph_data"])
        self.assertIn("delivered", metrics["graph_data"])
        self.assertIn("read", metrics["graph_data"])
        self.assertIn("clicked", metrics["graph_data"])

        self.assertEqual(
            metrics["graph_data"]["sent"]["value"],
            formatted_analytics_mock_data.get("status_count").get("sent").get("value"),
        )

        self.assertEqual(
            metrics["graph_data"]["delivered"]["value"],
            formatted_analytics_mock_data.get("status_count")
            .get("delivered")
            .get("value"),
        )
        self.assertEqual(
            metrics["graph_data"]["delivered"]["percentage"],
            formatted_analytics_mock_data.get("status_count")
            .get("delivered")
            .get("percentage"),
        )

        self.assertEqual(
            metrics["graph_data"]["read"]["value"],
            formatted_analytics_mock_data.get("status_count").get("read").get("value"),
        )
        self.assertEqual(
            metrics["graph_data"]["read"]["percentage"],
            formatted_analytics_mock_data.get("status_count")
            .get("read")
            .get("percentage"),
        )
        self.assertEqual(
            metrics["graph_data"]["clicked"]["value"],
            formatted_analytics_mock_data.get("status_count")
            .get("clicked")
            .get("value"),
        )
        self.assertEqual(
            metrics["graph_data"]["clicked"]["percentage"],
            formatted_analytics_mock_data.get("status_count")
            .get("clicked")
            .get("percentage"),
        )
