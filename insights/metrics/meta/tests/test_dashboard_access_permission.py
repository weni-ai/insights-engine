"""
Tests for DashboardAccessPermission to ensure it maintains the same logic
as the previous BaseFavoriteTemplateSerializer validation.
"""
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.metrics.meta.models import FavoriteTemplate
from insights.projects.models import Project, ProjectAuth


class TestDashboardAccessPermissionAddFavorites(APITestCase):
    """
    Tests for add_template_to_favorites endpoint with DashboardAccessPermission.
    Ensures the permission works the same as the old serializer validation.
    """

    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(user=self.user)

    def test_cannot_add_favorite_when_user_has_no_project_auth(self):
        """
        Test that a user without ProjectAuth cannot add favorites
        (same behavior as old serializer validation).
        """
        other_project = Project.objects.create(name="Other Project")
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=other_project,
        )

        response = self.client.post(
            "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
            {
                "dashboard": str(dashboard.uuid),
                "template_id": "1234567890987654",
            },
        )

        # Should be forbidden due to DashboardAccessPermission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_can_add_favorite_when_user_has_project_auth_role_1(self):
        """
        Test that a user with ProjectAuth (role=1) CAN add favorites.
        This validates the permission allows access like the old serializer.
        """
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        # Mock the template preview to avoid external API call
        with patch(
            "insights.metrics.meta.services.MetaMessageTemplatesService.get_template_preview"
        ) as mock_preview:
            mock_preview.return_value = {
                "id": "1234567890987654",
                "name": "test_template",
            }

            response = self.client.post(
                "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
                {
                    "dashboard": str(dashboard.uuid),
                    "template_id": "1234567890987654",
                },
            )

        # Should be successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_add_favorite_when_user_has_project_auth_any_role(self):
        """
        Test that a user with ProjectAuth (any role, not just role=1) CAN add favorites.
        This is critical - the old serializer didn't filter by role,
        so the new permission shouldn't either.
        """
        # Create ProjectAuth with role=2 (not role=1)
        ProjectAuth.objects.create(project=self.project, user=self.user, role=2)

        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        with patch(
            "insights.metrics.meta.services.MetaMessageTemplatesService.get_template_preview"
        ) as mock_preview:
            mock_preview.return_value = {
                "id": "1234567890987654",
                "name": "test_template",
            }

            response = self.client.post(
                "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
                {
                    "dashboard": str(dashboard.uuid),
                    "template_id": "1234567890987654",
                },
            )

        # Should be successful even with role=2
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_validation_error_when_dashboard_not_provided(self):
        """
        Test that the permission raises validation error when dashboard is missing.
        """
        response = self.client.post(
            "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
            {
                "template_id": "1234567890987654",
            },
        )

        # Should return 400 with validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dashboard", response.data)


class TestDashboardAccessPermissionRemoveFavorites(APITestCase):
    """
    Tests for remove_template_from_favorites endpoint with DashboardAccessPermission.
    """

    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(user=self.user)

    def test_cannot_remove_favorite_when_user_has_no_project_auth(self):
        """
        Test that a user without ProjectAuth cannot remove favorites.
        """
        other_project = Project.objects.create(name="Other Project")
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=other_project,
        )

        FavoriteTemplate.objects.create(
            dashboard=dashboard,
            template_id="1234567890987654",
            name="test_template",
        )

        response = self.client.post(
            "/v1/metrics/meta/whatsapp-message-templates/remove-template-from-favorites/",
            {
                "dashboard": str(dashboard.uuid),
                "template_id": "1234567890987654",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_can_remove_favorite_when_user_has_project_auth(self):
        """
        Test that a user with ProjectAuth CAN remove favorites.
        """
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        FavoriteTemplate.objects.create(
            dashboard=dashboard,
            template_id="1234567890987654",
            name="test_template",
        )

        response = self.client.post(
            "/v1/metrics/meta/whatsapp-message-templates/remove-template-from-favorites/",
            {
                "dashboard": str(dashboard.uuid),
                "template_id": "1234567890987654",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestDashboardAccessPermissionGetFavorites(APITestCase):
    """
    Tests for get_favorite_templates endpoint with DashboardAccessPermission.
    This endpoint uses query params instead of request body.
    """

    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(user=self.user)

    def test_cannot_get_favorites_when_user_has_no_project_auth(self):
        """
        Test that a user without ProjectAuth cannot get favorites via query params.
        """
        other_project = Project.objects.create(name="Other Project")
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=other_project,
        )

        response = self.client.get(
            "/v1/metrics/meta/whatsapp-message-templates/favorites/",
            {"dashboard": str(dashboard.uuid)},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_can_get_favorites_when_user_has_project_auth(self):
        """
        Test that a user with ProjectAuth CAN get favorites.
        Tests that permission works with query params (GET requests).
        """
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            config={"waba_id": "1234567890987654"},
        )

        FavoriteTemplate.objects.create(
            dashboard=dashboard,
            template_id="1234567890987654",
            name="test_template",
        )

        response = self.client.get(
            "/v1/metrics/meta/whatsapp-message-templates/favorites/",
            {"dashboard": str(dashboard.uuid)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_can_get_favorites_with_any_role(self):
        """
        Test that permission works with any ProjectAuth role (not just role=1).
        """
        ProjectAuth.objects.create(project=self.project, user=self.user, role=3)

        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            config={"waba_id": "1234567890987654"},
        )

        response = self.client.get(
            "/v1/metrics/meta/whatsapp-message-templates/favorites/",
            {"dashboard": str(dashboard.uuid)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestDashboardAccessPermissionLogicConsistency(APITestCase):
    """
    Tests to ensure DashboardAccessPermission logic exactly matches
    the old BaseFavoriteTemplateSerializer._get_dashboard_queryset() logic.
    """

    def setUp(self):
        self.user1 = User.objects.create(email="user1@test.com")
        self.user2 = User.objects.create(email="user2@test.com")

        self.project1 = Project.objects.create(name="Project 1")
        self.project2 = Project.objects.create(name="Project 2")

        # user1 has access to project1 only
        ProjectAuth.objects.create(project=self.project1, user=self.user1, role=1)

        # user2 has access to project2 only
        ProjectAuth.objects.create(project=self.project2, user=self.user2, role=1)

    def test_user_can_only_access_dashboards_from_authorized_projects(self):
        """
        Test that users can ONLY access dashboards from projects they have ProjectAuth for.
        This validates the filtering logic: project__in=ProjectAuth.objects.filter(user=user)
        """
        self.client.force_authenticate(user=self.user1)

        dashboard1 = Dashboard.objects.create(
            name="Dashboard 1",
            project=self.project1,
        )
        dashboard2 = Dashboard.objects.create(
            name="Dashboard 2",
            project=self.project2,
        )

        with patch(
            "insights.metrics.meta.services.MetaMessageTemplatesService.get_template_preview"
        ) as mock_preview:
            mock_preview.return_value = {
                "id": "1234567890987654",
                "name": "test_template",
            }

            # Should succeed for dashboard1 (user1 has access to project1)
            response1 = self.client.post(
                "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
                {
                    "dashboard": str(dashboard1.uuid),
                    "template_id": "1234567890987654",
                },
            )
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            # Should fail for dashboard2 (user1 does NOT have access to project2)
            response2 = self.client.post(
                "/v1/metrics/meta/whatsapp-message-templates/add-template-to-favorites/",
                {
                    "dashboard": str(dashboard2.uuid),
                    "template_id": "9876543210123456",
                },
            )
            self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

    def test_multiple_users_isolated_access(self):
        """
        Test that different users have isolated access based on their ProjectAuth.
        """
        dashboard1 = Dashboard.objects.create(
            name="Dashboard 1",
            project=self.project1,
        )

        # user1 should have access
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get(
            "/v1/metrics/meta/whatsapp-message-templates/favorites/",
            {"dashboard": str(dashboard1.uuid)},
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # user2 should NOT have access
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get(
            "/v1/metrics/meta/whatsapp-message-templates/favorites/",
            {"dashboard": str(dashboard1.uuid)},
        )
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

