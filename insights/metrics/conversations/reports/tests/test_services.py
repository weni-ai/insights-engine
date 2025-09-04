from django.test import TestCase


from insights.metrics.conversations.reports.services import (
    ConversationsReportService,
)


class TestConversationsReportService(TestCase):
    def setUp(self):
        self.service = ConversationsReportService()

    def test_send_email(self):
        pass
