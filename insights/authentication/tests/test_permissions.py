from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from insights.authentication.permissions import (
    ProjectAuthBodyPermission,
    ProjectAuthPermission,
    ProjectAuthQueryParamPermission,
    ProjectQueryParamPermission,
)
from insights.authentication.services.project_auth import EXISTING_ROLES
from insights.projects.models import Project, ProjectAuth
from insights.users.models import User


def _viewer_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "user": "viewer@x.com",
        "project_authorization": EXISTING_ROLES["viewer"],
    }
    return response


def _denied_response():
    response = MagicMock()
    response.status_code = 404
    response.json.return_value = {}
    return response


def _build_request(*, user, method="GET", token="Bearer t", query_params=None, data=None):
    """Build a request-like object good enough for the permission classes."""
    request = MagicMock()
    request.user = user
    request.method = method
    request.headers = {"Authorization": token} if token else {}
    request.query_params = query_params or {}
    request.data = data or {}
    return request


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class ProjectAuthPermissionTests(TestCase):
    def setUp(self):
        self.permission = ProjectAuthPermission()
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create_user(email="someone@x.com")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_admin_local_passes_without_external_call(self, mock_get):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = _build_request(user=self.user, method="GET")

        self.assertTrue(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )
        mock_get.assert_not_called()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_admin_local_passes_on_post_without_external_call(self, mock_get):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = _build_request(user=self.user, method="POST")

        self.assertTrue(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )
        mock_get.assert_not_called()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_passes_on_get(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(user=self.user, method="GET")

        self.assertTrue(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )
        mock_get.assert_called_once()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_blocked_on_post(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(user=self.user, method="POST")

        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_blocked_on_put(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(user=self.user, method="PUT")

        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_blocked_on_delete(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(user=self.user, method="DELETE")

        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_no_external_authorization_blocked(self, mock_get):
        mock_get.return_value = _denied_response()
        request = _build_request(user=self.user, method="GET")

        self.assertFalse(
            self.permission.has_object_permission(request, view=None, obj=self.project)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_object_with_project_attribute(self, mock_get):
        """Permission should resolve project from obj.project when obj is not a Project."""
        mock_get.return_value = _viewer_response()
        obj = MagicMock()
        obj.project = self.project
        request = _build_request(user=self.user, method="GET")

        self.assertTrue(
            self.permission.has_object_permission(request, view=None, obj=obj)
        )


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class ProjectAuthQueryParamPermissionTests(TestCase):
    def setUp(self):
        self.permission = ProjectAuthQueryParamPermission()
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create_user(email="someone@x.com")
        self.view = MagicMock(project_uuid_field="project_uuid")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_admin_local_passes_without_external_call(self, mock_get):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
        )

        self.assertTrue(self.permission.has_permission(request, self.view))
        mock_get.assert_not_called()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_passes_on_get(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
        )

        self.assertTrue(self.permission.has_permission(request, self.view))

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_blocked_on_post(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="POST",
            query_params={"project_uuid": str(self.project.uuid)},
        )

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_missing_project_uuid_raises_validation_error(self):
        request = _build_request(user=self.user, method="GET", query_params={})

        with self.assertRaises(ValidationError):
            self.permission.has_permission(request, self.view)


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class ProjectAuthBodyPermissionTests(TestCase):
    def setUp(self):
        self.permission = ProjectAuthBodyPermission()
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create_user(email="someone@x.com")
        self.view = MagicMock()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_admin_local_passes_without_external_call(self, mock_get):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = _build_request(
            user=self.user,
            method="POST",
            data={"project_uuid": str(self.project.uuid)},
        )

        self.assertTrue(self.permission.has_permission(request, self.view))
        mock_get.assert_not_called()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_non_safe_method_blocked_for_viewer(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="POST",
            data={"project_uuid": str(self.project.uuid)},
        )

        self.assertFalse(self.permission.has_permission(request, self.view))

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_safe_method_passes_for_viewer(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="GET",
            data={"project_uuid": str(self.project.uuid)},
        )

        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_missing_project_uuid_raises_validation_error(self):
        request = _build_request(user=self.user, method="POST", data={})

        with self.assertRaises(ValidationError):
            self.permission.has_permission(request, self.view)


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class ProjectQueryParamPermissionTests(TestCase):
    def setUp(self):
        self.permission = ProjectQueryParamPermission()
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create_user(email="someone@x.com")
        self.view = MagicMock()

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_passes_on_get(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
        )

        self.assertTrue(self.permission.has_permission(request, self.view))

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_viewer_blocked_without_token(self, mock_get):
        mock_get.return_value = _viewer_response()
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
            token=None,
        )

        self.assertFalse(self.permission.has_permission(request, self.view))
        mock_get.assert_not_called()

    def test_local_admin_passes_without_external_call(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
            token=None,
        )

        with patch(
            "insights.authentication.services.project_auth.requests.get"
        ) as mock_get:
            self.assertTrue(self.permission.has_permission(request, self.view))
            mock_get.assert_not_called()

    def test_non_admin_local_project_auth_is_denied_without_external(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=0)
        request = _build_request(
            user=self.user,
            method="GET",
            query_params={"project_uuid": str(self.project.uuid)},
            token=None,
        )

        with patch(
            "insights.authentication.services.project_auth.requests.get"
        ) as mock_get:
            self.assertFalse(self.permission.has_permission(request, self.view))
            mock_get.assert_not_called()
