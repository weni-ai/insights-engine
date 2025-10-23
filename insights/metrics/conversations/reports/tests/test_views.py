from unittest.mock import patch
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.projects.models import Project
from insights.authentication.tests.decorators import with_project_auth
from insights.reports.choices import ReportStatus, ReportSource, ReportFormat
from insights.reports.models import Report
from insights.widgets.models import Widget


class BaseTestConversationsReportsViewSet(APITestCase):
    def get_status(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/report/"

        return self.client.get(url, query_params)

    def request_generation(self, data: dict) -> Response:
        url = "/v1/metrics/conversations/report/"

        return self.client.post(url, data)


class TestConversationsReportsViewSetAsAnonymousUser(
    BaseTestConversationsReportsViewSet
):
    def test_get_status_when_user_is_anonymous(self):
        response = self.get_status({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_generation_when_user_is_anonymous(self):
        response = self.request_generation({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsReportsViewSetAsAuthenticatedUser(
    BaseTestConversationsReportsViewSet
):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name=CONVERSATIONS_DASHBOARD_NAME, project=self.project
        )
        self.client.force_authenticate(self.user)

    def test_get_status_without_project_uuid(self):
        response = self.get_status({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_get_status_without_project_permission(self):
        response = self.get_status({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_current_report_for_project"
    )
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_get_status_without_report(
        self, mock_is_feature_active, mock_get_current_report_for_project
    ):
        mock_is_feature_active.return_value = True
        mock_get_current_report_for_project.return_value = None

        response = self.get_status({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReportStatus.READY)

        mock_get_current_report_for_project.assert_called_once_with(self.project)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_current_report_for_project"
    )
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_get_status_with_report(
        self, mock_is_feature_active, mock_get_current_report_for_project
    ):
        mock_is_feature_active.return_value = True
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

    def test_request_generation_without_project_uuid(self):
        response = self.request_generation({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_request_generation_without_project_permission(self):
        response = self.request_generation({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_request_generation_without_feature_flag_permission(
        self, mock_is_feature_active
    ):
        mock_is_feature_active.return_value = False

        response = self.request_generation({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        mock_is_feature_active.assert_called_once_with(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            self.user.email,
            self.project.uuid,
        )

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_current_report_for_project"
    )
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.request_generation"
    )
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_request_generation(
        self,
        mock_is_feature_active,
        mock_request_generation,
        mock_get_current_report_for_project,
    ):
        report = Report(
            project=self.project,
            source=ReportSource.CONVERSATIONS_DASHBOARD,
            status=ReportStatus.PENDING,
            requested_by=self.user,
        )
        mock_is_feature_active.return_value = True
        mock_request_generation.return_value = report
        mock_get_current_report_for_project.return_value = None

        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "type": "CSAT",
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        response = self.request_generation(
            {
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "sections": ["RESOLUTIONS", "CSAT_AI"],
                "custom_widgets": [],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.assertEqual(response.data["status"], ReportStatus.PENDING)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["report_uuid"], str(report.uuid))

        mock_is_feature_active.assert_called_once_with(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            self.user.email,
            self.project.uuid,
        )


class BaseTestAvailableWidgetsViewSet(APITestCase):
    def get_available_widgets(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/report/available-widgets/"
        return self.client.get(url, query_params)


class TestAvailableWidgetsViewSetAsAnonymousUser(BaseTestAvailableWidgetsViewSet):
    def test_get_available_widgets_when_user_is_anonymous(self):
        response = self.get_available_widgets({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAvailableWidgetsViewSetAsAuthenticatedUser(BaseTestAvailableWidgetsViewSet):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(self.user)

    def test_get_available_widgets_without_project_uuid(self):
        response = self.get_available_widgets({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_get_available_widgets_without_project_permission(self):
        response = self.get_available_widgets({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_get_available_widgets_without_feature_flag_permission(
        self, mock_is_feature_active
    ):
        mock_is_feature_active.return_value = False

        response = self.get_available_widgets({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_is_feature_active.assert_called_once_with(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            self.user.email,
            self.project.uuid,
        )

    def test_get_available_widgets_with_invalid_project_uuid(self):
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.get_available_widgets({"project_uuid": invalid_uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_available_widgets"
    )
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_get_available_widgets_success(
        self, mock_is_feature_active, mock_get_available_widgets
    ):
        mock_is_feature_active.return_value = True
        mock_widgets = {
            "sections": ["RESOLUTIONS", "CSAT_AI", "NPS_AI"],
            "custom_widgets": [str(uuid.uuid4()), str(uuid.uuid4())],
        }
        mock_get_available_widgets.return_value = mock_widgets

        response = self.get_available_widgets({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sections"], mock_widgets["sections"])
        self.assertEqual(
            response.data["custom_widgets"], mock_widgets["custom_widgets"]
        )
        mock_get_available_widgets.assert_called_once_with(project=self.project)
        mock_is_feature_active.assert_called_once_with(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            self.user.email,
            self.project.uuid,
        )

    @with_project_auth
    @patch(
        "insights.metrics.conversations.reports.services.ConversationsReportService.get_available_widgets"
    )
    @patch("insights.metrics.conversations.reports.permissions.is_feature_active")
    def test_get_available_widgets_empty_response(
        self, mock_is_feature_active, mock_get_available_widgets
    ):
        mock_is_feature_active.return_value = True
        mock_widgets = {"sections": [], "custom_widgets": []}
        mock_get_available_widgets.return_value = mock_widgets

        response = self.get_available_widgets({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sections"], [])
        self.assertEqual(response.data["custom_widgets"], [])
        mock_get_available_widgets.assert_called_once_with(project=self.project)
        mock_is_feature_active.assert_called_once_with(
            settings.CONVERSATIONS_REPORT_FEATURE_FLAG_KEY,
            self.user.email,
            self.project.uuid,
        )
