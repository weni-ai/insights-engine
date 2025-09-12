from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


class TestFeatureFlagCheck(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com")
        self.project = Project.objects.create(name="P1")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("feature_flags:check")

    def test_requires_project_uuid(self):
        response = self.client.get(self.url, {"feature": "flag"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @with_project_auth
    @patch("insights.feature_flags.views.FeatureFlagClient.is_on", return_value=True)
    def test_ok(self, _mock_is_on):
        resp = self.client.get(self.url, {"feature": "flag", "project_uuid": str(self.project.uuid)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"feature": "flag", "on": True})