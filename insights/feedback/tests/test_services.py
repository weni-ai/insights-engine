from django.test import TestCase
from datetime import datetime


from django.utils import timezone
from django.utils.timezone import timedelta

from django.test import override_settings
from insights.dashboards.models import Dashboard
from insights.feedback.dataclass import SurveyStatus
from insights.feedback.models import Feedback, Survey
from insights.feedback.services import FeedbackService
from insights.users.models import User
from insights.projects.models import Project
from insights.feedback.choices import DashboardTypes


class TestFeedbackService(TestCase):
    def setUp(self):
        self.service = FeedbackService()

    def create_user(self, email: str):
        return User.objects.create(email=email)

    def create_dashboard(self):
        return Dashboard.objects.create(
            name="Test Dashboard", project=Project.objects.create(name="Test Project")
        )

    def create_survey(
        self,
        start: datetime = timezone.now() - timedelta(days=1),
        end: datetime = timezone.now() + timedelta(days=1),
    ):
        return Survey.objects.create(
            start=start,
            end=end,
        )

    def test_get_current_survey_when_no_survey_exists(self):
        survey = self.service.get_current_survey()

        self.assertIsNone(survey)

    def test_get_current_survey_when_survey_is_in_the_past(self):
        survey = self.create_survey(
            start=timezone.now() - timedelta(days=4),
            end=timezone.now() - timedelta(days=3),
        )

        survey = self.service.get_current_survey()

        self.assertIsNone(survey)

    def test_get_current_survey_when_survey_is_in_the_future(self):
        survey = self.create_survey(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=2),
        )

        survey = self.service.get_current_survey()

        self.assertIsNone(survey)

    def test_get_current_survey_when_survey_exists(self):
        survey = self.create_survey()

        survey = self.service.get_current_survey()

        self.assertEqual(survey, survey)

    @override_settings(VTEX_INTERNAL_DOMAINS=["vtex.com"])
    def get_survey_status_when_user_is_vtex_internal(self):
        user = self.create_user(email="test@vtex.com")
        dashboard = self.create_dashboard()
        survey = self.create_survey()

        survey_status = self.service.get_survey_status(user, dashboard)

        self.assertEqual(
            survey_status, SurveyStatus(is_active=False, user_answered=False)
        )

    def test_get_survey_status_when_survey_does_not_exist(self):
        user = self.create_user(email="test@email.com")
        dashboard = self.create_dashboard()
        survey_status = self.service.get_survey_status(user, dashboard)

        self.assertEqual(
            survey_status, SurveyStatus(is_active=False, user_answered=False)
        )

    def test_get_survey_status_when_user_has_not_answered_the_survey(self):
        user = self.create_user(email="test@email.com")
        dashboard = self.create_dashboard()
        survey = self.create_survey()
        survey_status = self.service.get_survey_status(user, dashboard)

        self.assertEqual(
            survey_status,
            SurveyStatus(is_active=True, user_answered=False, uuid=survey.uuid),
        )

    def test_get_survey_status_when_user_has_answered_the_survey(self):
        user = self.create_user(email="test@email.com")
        dashboard = self.create_dashboard()
        survey = self.create_survey()
        Feedback.objects.create(
            survey=survey,
            user=user,
            dashboard=dashboard,
            dashboard_type=DashboardTypes.CONVERSATIONAL,
        )
        survey_status = self.service.get_survey_status(user, dashboard)

        self.assertEqual(
            survey_status,
            SurveyStatus(is_active=True, user_answered=True, uuid=survey.uuid),
        )
