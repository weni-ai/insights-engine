import uuid
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from insights.feature_flags.views import FeatureFlagsViewSet
from insights.projects.models import Project, ProjectAuth
from insights.users.models import User

TEST_URLCONF = "insights.feature_flags.tests.urls"


@override_settings(ROOT_URLCONF=TEST_URLCONF)
class FeatureFlagsViewSetAsAnonymousUserTestCase(APITestCase):
    def test_list_requires_authentication(self):
        url = reverse("feature_flags-list")

        response = self.client.get(url, {"project_uuid": str(uuid.uuid4())})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF=TEST_URLCONF)
class FeatureFlagsViewSetAsAuthenticatedUserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("feature_flags-list")

    def test_returns_bad_request_when_project_uuid_is_missing(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project_uuid", response.data)

    def test_returns_forbidden_when_user_has_no_project_auth(self):
        response = self.client.get(
            self.url, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_forbidden_when_project_does_not_exist(self):
        response = self.client.get(
            self.url, {"project_uuid": str(uuid.uuid4())}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _grant_project_auth(self):
        ProjectAuth.objects.create(
            project=self.project, user=self.user, role=1
        )

    @patch.object(FeatureFlagsViewSet, "service")
    def test_returns_active_features_for_authorized_user(self, mock_service):
        mock_service.get_active_feature_flags_for_attributes.return_value = [
            "feature_a",
            "feature_b",
        ]
        self._grant_project_auth()

        response = self.client.get(
            self.url, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"active_features": ["feature_a", "feature_b"]},
        )

    @patch.object(FeatureFlagsViewSet, "service")
    def test_service_is_called_with_user_and_project_attributes(
        self, mock_service
    ):
        mock_service.get_active_feature_flags_for_attributes.return_value = []
        self._grant_project_auth()

        self.client.get(self.url, {"project_uuid": str(self.project.uuid)})

        mock_service.get_active_feature_flags_for_attributes.assert_called_once_with(
            attributes={
                "userEmail": self.user.email,
                "projectUUID": str(self.project.uuid),
            }
        )

    @patch.object(FeatureFlagsViewSet, "service")
    def test_returns_empty_list_when_no_active_features(self, mock_service):
        mock_service.get_active_feature_flags_for_attributes.return_value = []
        self._grant_project_auth()

        response = self.client.get(
            self.url, {"project_uuid": str(self.project.uuid)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"active_features": []})

