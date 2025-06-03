from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth


class BaseTestDashboardViewSet(APITestCase):
    def list(self, filters: dict = None) -> Response:
        url = reverse("dashboard-list")

        return self.client.get(url, filters)


class TestDashboardViewSetAsAnonymousUser(BaseTestDashboardViewSet):
    def test_cannot_list_dashboards_when_unauthenticated(self):
        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDashboardViewSetAsAuthenticatedUser(BaseTestDashboardViewSet):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@test.com",
        )
        self.project = Project.objects.create(
            name="Test Project",
        )

        self.client.force_authenticate(user=self.user)

    @with_project_auth
    def test_list_dashboards(self):
        dashboard_1 = Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )

        # From another project, should not be listed
        dashboard_2 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=Project.objects.create(
                name="Test Project 2",
            ),
        )

        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_dashboards = {d["uuid"] for d in response.data["results"]}

        self.assertIn(str(dashboard_1.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_2.uuid), response_dashboards)

    def test_list_dashboards_without_project_auth(self):
        Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )
        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    @with_project_auth
    def test_list_dashboards_filtering_by_project(self):
        dashboard_1 = Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )

        project_2 = Project.objects.create(
            name="Test Project 2",
        )
        ProjectAuth.objects.create(project=project_2, user=self.user, role=1)
        dashboard_2 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=project_2,
        )

        # From another project, should not be listed
        dashboard_3 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=Project.objects.create(
                name="Test Project 2",
            ),
        )

        response = self.list({"project": str(self.project.uuid)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_dashboards = {d["uuid"] for d in response.data["results"]}

        self.assertIn(str(dashboard_1.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_2.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_3.uuid), response_dashboards)
