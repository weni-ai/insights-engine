from django.test import TestCase

from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self):
        self.project = Project.objects.create()
        self.start_date = "2021-01-01"
        self.end_date = "2021-01-02"

    # def test_get_timeseries(self):
    #     data = self.service.get_timeseries(
    #         project=self.project,
    #         start_date=self.start_date,
    #         end_date=self.end_date,
    #         unit="day",
    #     )
