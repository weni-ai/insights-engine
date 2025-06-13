from django.test import TestCase

from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self):
        self.project = Project.objects.create()
        self.start_date = "2021-01-01"
        self.end_date = "2021-01-02"

    def test_get_timeseries_for_day_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.DAY,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "total"
            ],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "by_human"
            ],
        )

    def test_get_timeseries_for_hour_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.HOUR,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["by_human"],
        )

    def test_get_timeseries_for_month_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.MONTH,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["by_human"],
        )
