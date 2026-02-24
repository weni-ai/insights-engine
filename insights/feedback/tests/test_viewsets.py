import uuid
from rest_framework.test import APITestCase
from rest_framework.response import Response
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from insights.feedback.choices import DashboardTypes
from insights.feedback.models import Feedback, Survey
from insights.users.models import User
from insights.projects.models import Project, ProjectAuth
from insights.dashboards.models import Dashboard


class BaseTestFeedbackViewSet(APITestCase):
    def check_survey(self, data: dict) -> Response:
        url = reverse("feedback-check-survey")

        return self.client.get(url, data)

    def create_feedback(self, data: dict) -> Response:
        url = reverse("feedback-list")

        return self.client.post(url, data, format="json")


class TestFeedbackViewSetAsAnonymousUser(BaseTestFeedbackViewSet):
    def test_check_survey_without_authentication(self):
        response = self.check_survey({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_feedback_without_authentication(self):
        response = self.create_feedback({})

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

    def test_create_feedback_when_no_data_is_provided(self):
        response = self.create_feedback({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["type"][0].code, "required")
        self.assertEqual(response.data["dashboard"][0].code, "required")
        self.assertEqual(response.data["survey"][0].code, "required")
        self.assertEqual(response.data["answers"][0].code, "required")

    def test_create_feedback_when_dashboard_type_is_invalid(self):
        response = self.create_feedback(
            {
                "type": "INVALID",
                "dashboard": uuid.uuid4(),
                "survey": uuid.uuid4(),
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["type"][0].code, "invalid_choice")

    def test_create_feedback_when_dashboard_does_not_exist(self):
        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": uuid.uuid4(),
                "survey": uuid.uuid4(),
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Dashboard not found")

    def test_create_feedback_when_dashboard_exists_but_user_does_not_have_permission(
        self,
    ):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": uuid.uuid4(),
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "User does not have permission to access this dashboard",
        )

    def test_create_feedback_when_dashboard_exists_and_user_has_not_admin_role(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=0)

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": uuid.uuid4(),
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "User does not have permission to access this dashboard",
        )

    def test_create_feedback_when_survey_does_not_exist(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": uuid.uuid4(),
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Survey not found")

    def test_create_feedback_when_survey_exists_but_is_not_active(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        survey = Survey.objects.create(
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() - timedelta(days=1),
        )

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": survey.uuid,
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Survey is not active")

    def test_create_feedback_when_survey_exists_and_is_active_but_user_has_already_answered_the_survey(
        self,
    ):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        survey = Survey.objects.create(
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() + timedelta(days=1),
        )

        Feedback.objects.create(
            survey=survey,
            user=self.user,
            dashboard=dashboard,
            dashboard_type=DashboardTypes.CONVERSATIONAL,
        )

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": survey.uuid,
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "User has already answered the survey")

    def test_create_feedback(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        survey = Survey.objects.create(
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() + timedelta(days=1),
        )

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": survey.uuid,
                "answers": [
                    {
                        "reference": "TRUST",
                        "answer": "1",
                        "type": "SCORE_1_5",
                    },
                    {
                        "reference": "MAKE_DECISION",
                        "answer": "1",
                        "type": "SCORE_1_5",
                    },
                    {
                        "reference": "ROI",
                        "answer": "1",
                        "type": "SCORE_1_5",
                    },
                    {
                        "reference": "COMMENT",
                        "answer": "test",
                        "type": "TEXT",
                    },
                ],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"], DashboardTypes.CONVERSATIONAL)
        self.assertEqual(response.data["dashboard"], str(dashboard.uuid))
        self.assertEqual(response.data["survey"], str(survey.uuid))
        self.assertEqual(len(response.data["answers"]), 4)
        self.assertEqual(response.data["answers"][0]["reference"], "TRUST")
        self.assertEqual(response.data["answers"][0]["answer"], "1")
        self.assertEqual(response.data["answers"][0]["type"], "SCORE_1_5")
        self.assertEqual(response.data["answers"][1]["reference"], "MAKE_DECISION")
        self.assertEqual(response.data["answers"][1]["answer"], "1")
        self.assertEqual(response.data["answers"][1]["type"], "SCORE_1_5")
        self.assertEqual(response.data["answers"][2]["reference"], "ROI")
        self.assertEqual(response.data["answers"][2]["answer"], "1")
        self.assertEqual(response.data["answers"][2]["type"], "SCORE_1_5")
        self.assertEqual(response.data["answers"][3]["reference"], "COMMENT")
        self.assertEqual(response.data["answers"][3]["answer"], "test")
        self.assertEqual(response.data["answers"][3]["type"], "TEXT")

    def test_create_feedback_when_answer_is_invalid(self):
        project = Project.objects.create(name="Test Project")
        dashboard = Dashboard.objects.create(name="Test Dashboard", project=project)

        ProjectAuth.objects.create(project=project, user=self.user, role=1)

        survey = Survey.objects.create(
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() + timedelta(days=1),
        )

        response = self.create_feedback(
            {
                "type": DashboardTypes.CONVERSATIONAL,
                "dashboard": dashboard.uuid,
                "survey": survey.uuid,
                "answers": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["MAKE_DECISION"][0].code, "required")
        self.assertEqual(response.data["ROI"][0].code, "required")
        self.assertEqual(response.data["TRUST"][0].code, "required")
        self.assertNotIn("COMMENT", response.data)
