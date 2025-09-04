from unittest.mock import patch

from django.test import TestCase

from insights.users.models import User
from insights.reports.models import Report
from insights.reports.choices import ReportFormat
from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
)
from insights.projects.models import Project


class TestConversationsReportService(TestCase):
    def setUp(self):
        self.service = ConversationsReportService()
        self.project = Project.objects.create(name="Test")
        self.user = User.objects.create(
            email="test@test.com",
            language="en",
        )

    @patch("django.core.mail.EmailMessage.send")
    def test_send_email(self, mock_send_email):
        mock_send_email.return_value = None

        report = Report.objects.create(
            project=self.project,
            source=self.service.source,
            source_config={},
            filters={},
            format=ReportFormat.CSV,
            requested_by=self.user,
        )

        self.service.send_email(report, "test")

        mock_send_email.assert_called_once_with(
            fail_silently=False,
        )
