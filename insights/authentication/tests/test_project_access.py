from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from insights.authentication.project_access import (
    get_dashboard_queryset_for_request,
    has_project_read_access,
    resolve_project_uuid_from_request,
)
from insights.authentication.services.project_auth import EXISTING_ROLES
from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth
from insights.users.models import User
from insights.widgets.models import Widget


def _viewer_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "user": "viewer@x.com",
        "project_authorization": EXISTING_ROLES["viewer"],
    }
    return response


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class ProjectAccessTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(email="viewer@x.com")
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Live desk", project=self.project
        )

    def _request(self, *, query_params=None, dashboard_pk=None):
        request = self.factory.get(
            "/dashboards/",
            query_params or {},
            HTTP_AUTHORIZATION="Bearer fake-token",
        )
        request.user = self.user
        if dashboard_pk:
            request.resolver_match = MagicMock(kwargs={"pk": dashboard_pk})
        return request

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_has_project_read_access_for_external_viewer(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = self._request()

        self.assertTrue(
            has_project_read_access(request, str(self.project.uuid))
        )

    def test_has_project_read_access_for_local_admin(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = self._request()
        request.headers = {}

        self.assertTrue(
            has_project_read_access(request, str(self.project.uuid))
        )

    def test_non_admin_local_project_auth_is_denied(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=0)
        request = self._request()
        request.headers = {}

        self.assertFalse(
            has_project_read_access(request, str(self.project.uuid))
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_get_dashboard_queryset_includes_external_viewer_project(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = self._request(
            query_params={"project": str(self.project.uuid)},
        )

        uuids = set(
            get_dashboard_queryset_for_request(request).values_list("uuid", flat=True)
        )

        self.assertIn(self.dashboard.uuid, uuids)

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_get_dashboard_queryset_resolves_project_from_dashboard_pk(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = self._request()

        uuids = set(
            get_dashboard_queryset_for_request(
                request, dashboard_pk=str(self.dashboard.uuid)
            ).values_list("uuid", flat=True)
        )

        self.assertIn(self.dashboard.uuid, uuids)

    def test_resolve_project_uuid_from_dashboard_pk(self):
        request = self._request()

        resolved = resolve_project_uuid_from_request(
            request, dashboard_pk=str(self.dashboard.uuid)
        )

        self.assertEqual(resolved, str(self.project.uuid))

    def test_resolve_project_uuid_from_widget_pk(self):
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="w",
            source="s",
            type="t",
            config={},
            position={},
        )
        request = self._request()

        resolved = resolve_project_uuid_from_request(
            request, widget_pk=str(widget.uuid)
        )

        self.assertEqual(resolved, str(self.project.uuid))

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_get_dashboard_queryset_resolves_project_from_widget_pk(self, mock_get):
        mock_get.return_value = _viewer_response()
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="w",
            source="s",
            type="t",
            config={},
            position={},
        )
        request = self._request()

        uuids = set(
            get_dashboard_queryset_for_request(
                request, widget_pk=str(widget.uuid)
            ).values_list("uuid", flat=True)
        )

        self.assertIn(self.dashboard.uuid, uuids)

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_auth_is_cached_per_request(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = self._request()

        has_project_read_access(request, str(self.project.uuid))
        has_project_read_access(request, str(self.project.uuid))

        mock_get.assert_called_once()
