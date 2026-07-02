from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings

from insights.core.prometheus.views import metrics_view


@override_settings(PROMETHEUS_AUTH_TOKEN="test-token")
class MetricsViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_forbidden_without_authorization_header(self):
        request = self.factory.get("/api/prometheus/metrics")

        response = metrics_view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), "Access denied")

    def test_returns_forbidden_with_invalid_token(self):
        request = self.factory.get(
            "/api/prometheus/metrics",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )

        response = metrics_view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), "Access denied")

    @patch.dict("os.environ", {"PROMETHEUS_AUTH_TOKEN": "test-token"})
    @patch("insights.core.prometheus.views.ExportToDjangoView")
    def test_returns_metrics_with_valid_token(self, mock_export):
        mock_export.return_value.status_code = 200
        request = self.factory.get(
            "/api/prometheus/metrics",
            HTTP_AUTHORIZATION="Bearer test-token",
        )

        response = metrics_view(request)

        mock_export.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)
