from unittest.mock import patch, MagicMock

from django.test import TestCase

from insights.metrics.meta.permissions import (
    ProjectWABAPermission,
    ProjectDashboardWABAPermission,
)


class TestProjectWABAPermission(TestCase):
    def setUp(self):
        self.permission = ProjectWABAPermission()
        self.request = MagicMock()
        self.view = MagicMock()

    def test_returns_false_when_project_uuid_missing(self):
        self.request.query_params = {"waba_id": "123"}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_returns_false_when_waba_id_missing(self):
        self.request.query_params = {"project_uuid": "some-uuid"}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_returns_false_when_both_params_missing(self):
        self.request.query_params = {}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch("insights.metrics.meta.permissions.WeniIntegrationsClient")
    def test_returns_true_when_waba_id_matches(self, mock_client_cls):
        self.request.query_params = {
            "project_uuid": "some-uuid",
            "waba_id": "waba-123",
        }
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_wabas_for_project.return_value = [
            {"waba_id": "waba-123"},
            {"waba_id": "waba-456"},
        ]

        self.assertTrue(self.permission.has_permission(self.request, self.view))

    @patch("insights.metrics.meta.permissions.WeniIntegrationsClient")
    def test_returns_false_when_waba_id_not_found(self, mock_client_cls):
        self.request.query_params = {
            "project_uuid": "some-uuid",
            "waba_id": "waba-999",
        }
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_wabas_for_project.return_value = [
            {"waba_id": "waba-123"},
        ]

        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch("insights.metrics.meta.permissions.WeniIntegrationsClient")
    def test_returns_false_on_value_error(self, mock_client_cls):
        self.request.query_params = {
            "project_uuid": "some-uuid",
            "waba_id": "waba-123",
        }
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_wabas_for_project.side_effect = ValueError("invalid")

        self.assertFalse(self.permission.has_permission(self.request, self.view))


class TestProjectDashboardWABAPermission(TestCase):
    def setUp(self):
        self.permission = ProjectDashboardWABAPermission()
        self.request = MagicMock()
        self.view = MagicMock(spec=[])

    def test_returns_false_when_project_uuid_missing(self):
        self.request.query_params = {"waba_id": "123"}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_returns_false_when_waba_id_missing(self):
        self.request.query_params = {"project_uuid": "some-uuid"}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_returns_false_when_both_params_missing(self):
        self.request.query_params = {}
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch("insights.metrics.meta.permissions.Dashboard.objects.filter")
    def test_returns_true_when_dashboard_exists(self, mock_filter):
        self.request.query_params = {
            "project_uuid": "some-uuid",
            "waba_id": "waba-123",
        }
        mock_filter.return_value.exists.return_value = True

        self.assertTrue(self.permission.has_permission(self.request, self.view))
        mock_filter.assert_called_once_with(
            project__uuid="some-uuid",
            config__is_whatsapp_integration=True,
            config__waba_id="waba-123",
        )

    @patch("insights.metrics.meta.permissions.Dashboard.objects.filter")
    def test_returns_false_when_dashboard_not_found(self, mock_filter):
        self.request.query_params = {
            "project_uuid": "some-uuid",
            "waba_id": "waba-123",
        }
        mock_filter.return_value.exists.return_value = False

        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch("insights.metrics.meta.permissions.Dashboard.objects.filter")
    def test_uses_custom_project_uuid_field_from_view(self, mock_filter):
        self.view = MagicMock()
        self.view.project_uuid_field = "custom_project_field"
        self.request.query_params = {
            "custom_project_field": "custom-uuid",
            "waba_id": "waba-789",
        }
        mock_filter.return_value.exists.return_value = True

        self.assertTrue(self.permission.has_permission(self.request, self.view))
        mock_filter.assert_called_once_with(
            project__uuid="custom-uuid",
            config__is_whatsapp_integration=True,
            config__waba_id="waba-789",
        )
