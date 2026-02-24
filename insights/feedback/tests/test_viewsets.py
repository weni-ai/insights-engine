import uuid
from rest_framework.test import APITestCase
from rest_framework.response import Response
from django.urls import reverse
from rest_framework import status

from insights.users.models import User
from insights.projects.models import Project, ProjectAuth
from insights.dashboards.models import Dashboard


class BaseTestFeedbackViewSet(APITestCase):
    def check_survey(self, data: dict) -> Response:
        url = reverse("feedback-check-survey")

        return self.client.get(url, data)


class TestFeedbackViewSetAsAnonymousUser(BaseTestFeedbackViewSet):
    def test_check_survey_without_authentication(self):
        response = self.check_survey({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestFeedbackViewSetAsAuthenticatedUser(BaseTestFeedbackViewSet):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com")
        self.client.force_authenticate(user=self.user)

    def test_check_survey_when_no_query_params_are_provided(self):
        response = self.check_survey({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["dashboard"][0].code, "required")

    def test_check_survey_when_dashboard_does_not_exist(self):
        response = self.check_survey(
            {
                "project_uuid": uuid.uuid4(),
                "dashboard": uuid.uuid4(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_check_survey_when_dashboard_exists_but_is_in_another_project(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        response = self.check_survey(
            {
                "project_uuid": uuid.uuid4(),
                "dashboard": dashboard.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_check_survey_when_dashboard_exists_but_user_does_not_have_permission(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        response = self.check_survey(
            {
                "project_uuid": project.uuid,
                "dashboard": dashboard.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_survey_when_dashboard_exists_and_user_has_not_admin_role(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=0)

        response = self.check_survey(
            {
                "project_uuid": project.uuid,
                "dashboard": dashboard.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_survey_when_dashboard_exists_and_user_has_admin_role(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        response = self.check_survey(
            {
                "project_uuid": project.uuid,
                "dashboard": dashboard.uuid,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_active"], False)
        self.assertEqual(response.data["user_answered"], False)
        self.assertIsNone(response.data["uuid"])
