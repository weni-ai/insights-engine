import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from insights.authentication.admin_sso import (
    AdminOIDCAuthenticationBackend,
    admin_oidc_logout,
    get_oidc_logout_url,
)
from insights.authentication.authentication import JWTAuthentication
from insights.authentication.permissions import (
    FeatureFlagPermission,
    HasInternalAuthenticationPermission,
    ProjectAuthBodyPermission,
    ProjectQueryParamPermission,
)
from insights.authentication.services.jwt_service import JWTService
from insights.authentication.services.tests.test_jwt_service import (
    generate_private_key,
    generate_private_key_pem,
    generate_public_key,
    generate_public_key_pem,
)
from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth

User = get_user_model()


TEST_PRIVATE_KEY = generate_private_key()
TEST_PRIVATE_KEY_PEM = generate_private_key_pem(TEST_PRIVATE_KEY)

TEST_PUBLIC_KEY = generate_public_key(TEST_PRIVATE_KEY)
TEST_PUBLIC_KEY_PEM = generate_public_key_pem(TEST_PUBLIC_KEY)


class MockJWTAuthenticationView(APIView):
    authentication_classes = [JWTAuthentication]
    # Same as internal VTEX/conversations views: allow when JWT set request.jwt_payload/project_uuid
    permission_classes = [HasInternalAuthenticationPermission]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class TestJWTAuthentication(APITestCase):
    def setUp(self):
        self.jwt_service = JWTService()

    @override_settings(ROOT_URLCONF="insights.authentication.tests.test_urls")
    @override_settings(JWT_SECRET_KEY=TEST_PRIVATE_KEY_PEM)
    @override_settings(JWT_PUBLIC_KEY=TEST_PUBLIC_KEY_PEM)
    def test_jwt_authentication(self):
        project = Project.objects.create(name="Test Project")
        token = self.jwt_service.generate_jwt_token(project_uuid=project.uuid)
        url = reverse("jwt-authentication-view")
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})

    @override_settings(ROOT_URLCONF="insights.authentication.tests.test_urls")
    @override_settings(JWT_SECRET_KEY=TEST_PRIVATE_KEY_PEM)
    @override_settings(JWT_PUBLIC_KEY=TEST_PUBLIC_KEY_PEM)
    def test_jwt_authentication_project_not_found(self):
        token = self.jwt_service.generate_jwt_token(project_uuid=uuid.uuid4())
        url = reverse("jwt-authentication-view")
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Project not found"})

    @override_settings(ROOT_URLCONF="insights.authentication.tests.test_urls")
    def test_jwt_authentication_missing_header(self):
        url = reverse("jwt-authentication-view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(ROOT_URLCONF="insights.authentication.tests.test_urls")
    def test_jwt_authentication_invalid_header(self):
        url = reverse("jwt-authentication-view")
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer invalid-token")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestProjectAuthBodyPermission(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = ProjectAuthBodyPermission()
        self.user = User.objects.create_user(email="body@test.com")
        self.project = Project.objects.create(name="Body Project")
        self.view = MagicMock()

    def _make_post_request(self, data):
        wsgi_request = self.factory.post("/", data={}, format="json")
        request = Request(wsgi_request)
        request.user = self.user
        request._full_data = data
        return request

    def test_missing_project_uuid_raises_validation_error(self):
        request = self._make_post_request({})
        with self.assertRaises(ValidationError) as ctx:
            self.permission.has_permission(request, self.view)
        self.assertIn("project_uuid", ctx.exception.detail)

    def test_valid_project_uuid_with_auth(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = self._make_post_request({"project_uuid": str(self.project.uuid)})
        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_valid_project_uuid_without_auth(self):
        request = self._make_post_request({"project_uuid": str(self.project.uuid)})
        self.assertFalse(self.permission.has_permission(request, self.view))


class TestProjectQueryParamPermission(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = ProjectQueryParamPermission()
        self.user = User.objects.create_user(email="qp@test.com")
        self.project = Project.objects.create(name="QP Project")
        self.view = MagicMock()

    def _make_request(self, method="get", **kwargs):
        fn = getattr(self.factory, method)
        wsgi_request = fn(**kwargs)
        request = Request(wsgi_request)
        return request

    def test_anonymous_user_returns_false(self):
        from django.contrib.auth.models import AnonymousUser

        request = self._make_request(path="/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_missing_project_uuid_raises_validation_error(self):
        request = self._make_request(path="/")
        request.user = self.user
        with self.assertRaises(ValidationError) as ctx:
            self.permission.has_permission(request, self.view)
        self.assertIn("project_uuid", ctx.exception.detail)

    def test_valid_auth(self):
        ProjectAuth.objects.create(project=self.project, user=self.user, role=1)
        request = self._make_request(path="/", data={"project_uuid": str(self.project.uuid)})
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, self.view))


class TestFeatureFlagPermission(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = FeatureFlagPermission()
        self.user = User.objects.create_user(email="ff@test.com")
        self.project = Project.objects.create(name="FF Project")

    def _make_request(self, method="get", **kwargs):
        fn = getattr(self.factory, method)
        wsgi_request = fn(**kwargs)
        request = Request(wsgi_request)
        return request

    def test_no_feature_flag_key_on_view(self):
        view = MagicMock(spec=[])
        request = self._make_request(path="/")
        request.user = self.user
        self.assertFalse(self.permission.has_permission(request, view))

    def test_missing_project_returns_false(self):
        view = MagicMock()
        view.feature_flag_key = "test_flag"
        view.kwargs = {}
        request = self._make_request(path="/")
        request.user = self.user
        self.assertFalse(self.permission.has_permission(request, view))

    @patch("insights.authentication.permissions.is_feature_active", return_value=True)
    def test_feature_active(self, mock_ff):
        view = MagicMock()
        view.feature_flag_key = "test_flag"
        view.kwargs = {}
        request = self._make_request(path="/", data={"project_uuid": str(self.project.uuid)})
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, view))
        mock_ff.assert_called_once_with(
            "test_flag", user=self.user.email, project=self.project.uuid
        )

    @patch("insights.authentication.permissions.is_feature_active", return_value=False)
    def test_feature_inactive(self, mock_ff):
        view = MagicMock()
        view.feature_flag_key = "test_flag"
        view.kwargs = {}
        request = self._make_request(path="/", data={"project_uuid": str(self.project.uuid)})
        request.user = self.user
        self.assertFalse(self.permission.has_permission(request, view))

    @patch("insights.authentication.permissions.is_feature_active", return_value=True)
    def test_get_project_from_dashboard_pk(self, mock_ff):
        dashboard = Dashboard.objects.create(
            project=self.project,
            name="Test Dashboard",
            description="desc",
        )
        view = MagicMock()
        view.feature_flag_key = "test_flag"
        view.kwargs = {"pk": str(dashboard.uuid)}
        request = self._make_request(path="/")
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, view))

    def test_get_project_from_request_body(self):
        view = MagicMock()
        view.feature_flag_key = "test_flag"
        view.kwargs = {}
        wsgi_request = self.factory.post("/", data={}, format="json")
        request = Request(wsgi_request)
        request._full_data = {"project_uuid": str(self.project.uuid)}
        request.user = self.user
        with patch(
            "insights.authentication.permissions.is_feature_active", return_value=True
        ) as mock_ff:
            self.assertTrue(self.permission.has_permission(request, view))
            mock_ff.assert_called_once_with(
                "test_flag", user=self.user.email, project=self.project.uuid
            )


class TestGetOidcLogoutUrl(TestCase):
    def _make_request(self):
        factory = RequestFactory()
        request = factory.get("/admin/logout/")
        request.session = {}
        return request

    @override_settings(OIDC_OP_LOGOUT_ENDPOINT="", LOGOUT_REDIRECT_URL="/admin/")
    def test_without_logout_endpoint(self):
        request = self._make_request()
        url = get_oidc_logout_url(request)
        self.assertEqual(url, request.build_absolute_uri("/admin/"))

    @override_settings(
        OIDC_OP_LOGOUT_ENDPOINT="https://idp.example.com/logout",
        LOGOUT_REDIRECT_URL="/admin/",
        OIDC_RP_CLIENT_ID="my-client",
    )
    def test_with_logout_endpoint_and_id_token(self):
        request = self._make_request()
        request.session["oidc_id_token"] = "tok123"
        url = get_oidc_logout_url(request)
        self.assertIn("https://idp.example.com/logout?", url)
        self.assertIn("post_logout_redirect_uri=", url)
        self.assertIn("id_token_hint=tok123", url)
        self.assertIn("client_id=my-client", url)

    @override_settings(
        OIDC_OP_LOGOUT_ENDPOINT="https://idp.example.com/logout",
        LOGOUT_REDIRECT_URL="/admin/",
    )
    def test_with_logout_endpoint_without_id_token(self):
        request = self._make_request()
        url = get_oidc_logout_url(request)
        self.assertIn("post_logout_redirect_uri=", url)
        self.assertNotIn("id_token_hint", url)


class TestAdminOidcLogout(TestCase):
    def _make_request(self, authenticated=True):
        factory = RequestFactory()
        request = factory.get("/admin/logout/")
        from django.contrib.sessions.backends.db import SessionStore

        request.session = SessionStore()
        if authenticated:
            user = User.objects.create_user(email=f"logout-{uuid.uuid4()}@test.com")
            request.user = user
        else:
            from django.contrib.auth.models import AnonymousUser

            request.user = AnonymousUser()
        return request

    @override_settings(OIDC_OP_LOGOUT_URL_METHOD="", LOGOUT_REDIRECT_URL="/admin/")
    def test_logout_without_oidc_method(self):
        request = self._make_request()
        response = admin_oidc_logout(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")

    @override_settings(
        OIDC_OP_LOGOUT_URL_METHOD="insights.authentication.admin_sso.get_oidc_logout_url",
        OIDC_OP_LOGOUT_ENDPOINT="https://idp.example.com/logout",
        LOGOUT_REDIRECT_URL="/admin/",
    )
    def test_logout_with_oidc_method_authenticated(self):
        request = self._make_request(authenticated=True)
        response = admin_oidc_logout(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://idp.example.com/logout", response.url)

    @override_settings(
        OIDC_OP_LOGOUT_URL_METHOD="insights.authentication.admin_sso.get_oidc_logout_url",
        LOGOUT_REDIRECT_URL="/admin/",
    )
    def test_logout_with_oidc_method_unauthenticated(self):
        request = self._make_request(authenticated=False)
        response = admin_oidc_logout(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")


class TestAdminOIDCAuthenticationBackend(TestCase):
    @patch.object(AdminOIDCAuthenticationBackend, "__init__", lambda self: None)
    def test_filter_users_by_claims_returns_only_staff(self):
        backend = AdminOIDCAuthenticationBackend()
        staff_user = User.objects.create_user(
            email="staff@test.com", is_staff=True
        )
        User.objects.create_user(email="regular@test.com", is_staff=False)

        all_users = User.objects.filter(email__in=["staff@test.com", "regular@test.com"])
        with patch.object(
            AdminOIDCAuthenticationBackend.__bases__[0],
            "filter_users_by_claims",
            return_value=all_users,
        ):
            result = backend.filter_users_by_claims({"email": "staff@test.com"})
            self.assertEqual(list(result), [staff_user])

    @patch.object(AdminOIDCAuthenticationBackend, "__init__", lambda self: None)
    def test_create_user_returns_none(self):
        backend = AdminOIDCAuthenticationBackend()
        self.assertIsNone(backend.create_user({"email": "new@test.com"}))
