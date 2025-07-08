from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
import uuid
import requests

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project
from insights.authentication.authentication import StaticTokenAuthentication
from insights.authentication.permissions import IsServiceAuthentication


class BaseProjectViewSetTestCase(APITestCase):
    def get_project(self, uuid: str) -> Response:
        url = reverse("project-detail", kwargs={"pk": uuid})

        return self.client.get(url)


class TestProjectViewSetAsAnonymousUser(BaseProjectViewSetTestCase):
    def test_cannot_get_project_as_anonymous_user(self):
        response = self.get_project("123e4567-e89b-12d3-a456-426614174000")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_retrieve_source_data_as_anonymous_user(self):
        url = reverse(
            "project-retrieve-source-data",
            kwargs={
                "pk": "123e4567-e89b-12d3-a456-426614174000",
                "source_slug": "test_source",
            },
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_verify_project_indexer_as_anonymous_user(self):
        url = reverse(
            "project-verify-project-indexer",
            kwargs={"pk": "123e4567-e89b-12d3-a456-426614174000"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_release_flows_dashboard_as_anonymous_user(self):
        url = reverse("project-release-flows-dashboard")
        response = self.client.post(
            url, {"project_uuid": "123e4567-e89b-12d3-a456-426614174000"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_allowed_projects_as_anonymous_user(self):
        url = reverse("project-get-allowed-projects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestProjectViewSetAsAuthenticatedUser(BaseProjectViewSetTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(user=self.user)

    @with_project_auth
    def test_get_project_as_authenticated_user(self):
        response = self.get_project(self.project.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    def test_retrieve_source_data_success(self):
        url = reverse(
            "project-retrieve-source-data",
            kwargs={"pk": self.project.uuid, "source_slug": "test_source"},
        )

        with patch("insights.projects.viewsets.get_source") as mock_get_source:
            mock_source_query = MagicMock()
            mock_source_query.execute.return_value = {"data": "test_data"}
            mock_get_source.return_value = mock_source_query

            response = self.client.post(
                url,
                {"operation": "list", "tags": "tag1,tag2", "op_field": "test_field"},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {"data": "test_data"})

            # Verify the source query was called with correct parameters
            mock_source_query.execute.assert_called_once()
            call_args = mock_source_query.execute.call_args
            self.assertEqual(call_args[1]["filters"]["project"], str(self.project.uuid))
            self.assertEqual(call_args[1]["operation"], "list")
            self.assertEqual(call_args[1]["query_kwargs"]["op_field"], "test_field")

    @with_project_auth
    def test_retrieve_source_data_source_not_found(self):
        url = reverse(
            "project-retrieve-source-data",
            kwargs={"pk": self.project.uuid, "source_slug": "non_existent_source"},
        )

        with patch("insights.projects.viewsets.get_source") as mock_get_source:
            mock_get_source.return_value = None

            response = self.client.post(url, {})

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(
                response.data["detail"],
                "could not find a source with the slug non_existent_source",
            )

    @with_project_auth
    def test_retrieve_source_data_with_query_params(self):
        url = reverse(
            "project-retrieve-source-data",
            kwargs={"pk": self.project.uuid, "source_slug": "test_source"},
        )

        with patch("insights.projects.viewsets.get_source") as mock_get_source:
            mock_source_query = MagicMock()
            mock_source_query.execute.return_value = {"data": "test_data"}
            mock_get_source.return_value = mock_source_query

            response = self.client.get(
                url,
                {"operation": "list", "tags": "tag1,tag2", "op_field": "test_field"},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    def test_retrieve_source_data_exception_handling(self):
        url = reverse(
            "project-retrieve-source-data",
            kwargs={"pk": self.project.uuid, "source_slug": "test_source"},
        )

        with patch("insights.projects.viewsets.get_source") as mock_get_source:
            mock_source_query = MagicMock()
            mock_source_query.execute.side_effect = Exception("Test error")
            mock_get_source.return_value = mock_source_query

            response = self.client.post(url, {})

            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertEqual(response.data["detail"], "Failed to retrieve source data")

    @with_project_auth
    def test_verify_project_indexer_allowed_in_settings(self):
        url = reverse(
            "project-verify-project-indexer", kwargs={"pk": self.project.uuid}
        )

        with patch("insights.projects.viewsets.settings") as mock_settings:
            mock_settings.PROJECT_ALLOW_LIST = [str(self.project.uuid)]

            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data)

    @with_project_auth
    def test_verify_project_indexer_allowed_by_is_allowed(self):
        url = reverse(
            "project-verify-project-indexer", kwargs={"pk": self.project.uuid}
        )

        # Set project as allowed
        self.project.is_allowed = True
        self.project.save()

        with patch("insights.projects.viewsets.settings") as mock_settings:
            mock_settings.PROJECT_ALLOW_LIST = []

            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data)

    @with_project_auth
    def test_verify_project_indexer_not_allowed(self):
        url = reverse(
            "project-verify-project-indexer", kwargs={"pk": self.project.uuid}
        )

        # Ensure project is not allowed
        self.project.is_allowed = False
        self.project.save()

        with patch("insights.projects.viewsets.settings") as mock_settings:
            mock_settings.PROJECT_ALLOW_LIST = []

            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data)

    def test_release_flows_dashboard_missing_project_uuid(self):
        url = reverse("project-release-flows-dashboard")

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "project_uuid is required")

    def test_release_flows_dashboard_project_not_found(self):
        url = reverse("project-release-flows-dashboard")

        response = self.client.post(url, {"project_uuid": str(uuid.uuid4())})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Project not found")

    @patch("insights.projects.viewsets.requests.post")
    def test_release_flows_dashboard_success(self, mock_post):
        url = reverse("project-release-flows-dashboard")

        # Create a project that's not allowed initially
        project = Project.objects.create(name="Test Project", is_allowed=False)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch("insights.projects.viewsets.settings") as mock_settings:
            mock_settings.WEBHOOK_URL = "http://test-webhook.com"
            mock_settings.STATIC_TOKEN = "test-token"

            response = self.client.post(url, {"project_uuid": str(project.uuid)})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["success"], True)

            # Verify project was updated
            project.refresh_from_db()
            self.assertTrue(project.is_allowed)

            # Verify webhook was called
            mock_post.assert_called_once_with(
                "http://test-webhook.com",
                json={"project_uuid": str(project.uuid)},
                headers={"Authorization": "Bearer test-token"},
            )

    def test_release_flows_dashboard_generic_exception(self):
        url = reverse("project-release-flows-dashboard")
        with patch("insights.projects.viewsets.Project.objects.get") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            response = self.client.post(url, {"project_uuid": str(uuid.uuid4())})
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertEqual(
                response.data["detail"],
                "An internal error occurred while processing your request.",
            )

    def test_release_flows_dashboard_project_does_not_exist(self):
        url = reverse("project-release-flows-dashboard")
        with patch("insights.projects.viewsets.Project.objects.get") as mock_get:
            mock_get.side_effect = Project.DoesNotExist()
            response = self.client.post(url, {"project_uuid": str(uuid.uuid4())})
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["detail"], "Project not found")

    def test_get_allowed_projects_unauthorized(self):
        url = reverse("project-get-allowed-projects")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_allowed_projects_success(self):
        url = reverse("project-get-allowed-projects")
        allowed_project1 = Project.objects.create(
            name="Allowed Project 1", is_allowed=True
        )
        allowed_project2 = Project.objects.create(
            name="Allowed Project 2", is_allowed=True
        )
        not_allowed_project = Project.objects.create(
            name="Not Allowed Project", is_allowed=False
        )

        with patch(
            "insights.authentication.authentication.settings"
        ) as mock_settings, patch.object(
            StaticTokenAuthentication, "authenticate", return_value=(None, "service")
        ), patch.object(
            IsServiceAuthentication, "has_permission", return_value=True
        ):
            mock_settings.STATIC_API_TOKEN = "test-token"
            response = self.client.get(url, HTTP_AUTHORIZATION="Token test-token")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 2)
            # Convert UUIDs to strings for comparison
            project_uuids = [str(item["uuid"]) for item in response.data]
            self.assertIn(str(allowed_project1.uuid), project_uuids)
            self.assertIn(str(allowed_project2.uuid), project_uuids)
            self.assertNotIn(str(not_allowed_project.uuid), project_uuids)

    @patch("insights.projects.viewsets.requests.post")
    def test_release_flows_dashboard_webhook_failure(self, mock_post):
        url = reverse("project-release-flows-dashboard")

        # Create a project that's not allowed initially
        project = Project.objects.create(name="Test Project", is_allowed=False)

        # Mock the webhook to fail with a RequestException
        mock_post.side_effect = requests.exceptions.RequestException("Webhook error")

        with patch("insights.projects.viewsets.settings") as mock_settings:
            mock_settings.WEBHOOK_URL = "http://test-webhook.com"
            mock_settings.STATIC_TOKEN = "test-token"

            response = self.client.post(url, {"project_uuid": str(project.uuid)})

            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertEqual(
                response.data["detail"], "Failed to process webhook request"
            )

            # Verify project was reverted to original state
            project.refresh_from_db()
            self.assertFalse(project.is_allowed)
