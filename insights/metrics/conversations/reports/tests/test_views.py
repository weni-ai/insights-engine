from unittest.mock import patch


from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.projects.models import Project
from insights.authentication.tests.decorators import with_project_auth
from insights.reports.choices import ReportStatus, ReportSource
from insights.reports.models import Report


class BaseTestConversationsReportsViewSet(APITestCase):
    def get_status(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/report/"

        return self.client.get(url, query_params)


class TestConversationsReportsViewSetAsAnonymousUser(
    BaseTestConversationsReportsViewSet
):
    def test_get_status_when_user_is_anonymous(self):
        response = self.get_status({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsReportsViewSetAsAuthenticatedUser(
    BaseTestConversationsReportsViewSet
):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(self.user)

    def test_get_status_without_project_uuid(self):
        response = self.get_status({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_get_status_without_permission(self):
        response = self.get_status({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_current_report_for_project"
    )
    def test_get_status_without_report(self, mock_get_current_report_for_project):
        mock_get_current_report_for_project.return_value = None

        response = self.get_status({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReportStatus.READY)

        mock_get_current_report_for_project.assert_called_once_with(self.project)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_current_report_for_project"
    )
    def test_get_status_with_report(self, mock_get_current_report_for_project):
        report = Report.objects.create(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            status=ReportStatus.PENDING,
            requested_by=self.user,
        )
        mock_get_current_report_for_project.return_value = report

        response = self.get_status({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReportStatus.PENDING)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["report_uuid"], str(report.uuid))

        mock_get_current_report_for_project.assert_called_once_with(self.project)
