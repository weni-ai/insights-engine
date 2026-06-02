from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from insights.authentication.services.exceptions import ProjectAuthorizationDenied
from insights.authentication.services.project_auth import (
    EXISTING_ROLES,
    _check_project_authorization,
    has_external_general_project_permission,
)
from insights.projects.models import ProjectAuth


def _make_response(status_code: int = 200, payload: dict | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    return response


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class CheckProjectAuthorizationTests(TestCase):
    def setUp(self):
        self.token = "Bearer fake-token"
        self.project_uuid = "11111111-1111-1111-1111-111111111111"

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_safe_method_returns_authorized(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        authorized, user_email = _check_project_authorization(
            self.token, self.project_uuid, "GET"
        )

        self.assertTrue(authorized)
        self.assertEqual(user_email, "viewer@x.com")
        mock_get.assert_called_once_with(
            f"http://fake-auth/v2/projects/{self.project_uuid}/authorization",
            headers={"Authorization": self.token},
            timeout=3,
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_head_returns_authorized(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        authorized, _ = _check_project_authorization(
            self.token, self.project_uuid, "HEAD"
        )

        self.assertTrue(authorized)

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_post_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "POST")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_put_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "PUT")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_patch_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "PATCH")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_viewer_with_delete_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "DELETE")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_moderator_role_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "mod@x.com",
                "project_authorization": EXISTING_ROLES["moderator"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "GET")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_contributor_role_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "contributor@x.com",
                "project_authorization": EXISTING_ROLES["contributor"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "GET")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_not_set_role_raises_denied(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "user@x.com",
                "project_authorization": EXISTING_ROLES["not_set"],
            },
        )

        with self.assertRaises(ProjectAuthorizationDenied):
            _check_project_authorization(self.token, self.project_uuid, "GET")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_non_200_response_raises_does_not_exist(self, mock_get):
        mock_get.return_value = _make_response(status_code=404)

        with self.assertRaises(ProjectAuth.DoesNotExist):
            _check_project_authorization(self.token, self.project_uuid, "GET")

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_request_exception_propagates(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(requests.ConnectionError):
            _check_project_authorization(self.token, self.project_uuid, "GET")


@override_settings(
    PROJECT_AUTH_API_BASE_URL="http://fake-auth",
    PROJECT_AUTH_API_TIMEOUT=3,
)
class HasExternalGeneralProjectPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.project_uuid = "11111111-1111-1111-1111-111111111111"

    def test_returns_false_when_no_authorization_header(self):
        request = self.factory.get("/whatever")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_true_for_viewer_on_get(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        self.assertTrue(
            has_external_general_project_permission(request, self.project_uuid)
        )
        self.assertEqual(
            getattr(request, "project_auth_user_email", None), "viewer@x.com"
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_false_for_viewer_on_post(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )
        request = self.factory.post("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_false_for_non_viewer_role(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "mod@x.com",
                "project_authorization": EXISTING_ROLES["moderator"],
            },
        )
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_false_when_external_service_unavailable(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("boom")
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_false_when_response_is_404(self, mock_get):
        mock_get.return_value = _make_response(status_code=404)
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_false_when_token_user_does_not_match_request_user(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "tokenowner@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")
        request.user = MagicMock(email="impersonated@x.com")

        self.assertFalse(
            has_external_general_project_permission(request, self.project_uuid)
        )
        self.assertIsNone(getattr(request, "project_auth_user_email", None))

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_returns_true_when_token_user_matches_request_user(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")
        request.user = MagicMock(email="viewer@x.com")

        self.assertTrue(
            has_external_general_project_permission(request, self.project_uuid)
        )

    @patch("insights.authentication.services.project_auth.requests.get")
    def test_external_auth_result_is_cached_per_request(self, mock_get):
        mock_get.return_value = _make_response(
            status_code=200,
            payload={
                "user": "viewer@x.com",
                "project_authorization": EXISTING_ROLES["viewer"],
            },
        )
        request = self.factory.get("/whatever", HTTP_AUTHORIZATION="Bearer fake-token")

        has_external_general_project_permission(request, self.project_uuid)
        has_external_general_project_permission(request, self.project_uuid)

        mock_get.assert_called_once()
