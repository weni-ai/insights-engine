import datetime

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from insights.metrics.meta.serializers import (
    TemplatesMetricsAnalyticsQueryParamsSerializer,
)


class TestTemplatesMetricsAnalyticsQueryParamsSerializer(TestCase):
    def test_validate_start_date_after_end_date(self):
        serializer = TemplatesMetricsAnalyticsQueryParamsSerializer(
            data={
                "start_date": "2023-01-02T00:00:00Z",
                "end_date": "2023-01-01T00:00:00Z",
                "waba_id": "123",
            }
        )
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("start_date", context.exception.detail)
        self.assertEqual(
            context.exception.detail["start_date"][0],
            "Start date must be before end date",
        )

    def test_validate_analytics_selected_period_called(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        start_date = now - datetime.timedelta(days=1)
        end_date = now

        serializer = TemplatesMetricsAnalyticsQueryParamsSerializer(
            data={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "waba_id": "123",
            }
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_valid_data(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        start_date = now - datetime.timedelta(days=1)
        end_date = now

        serializer = TemplatesMetricsAnalyticsQueryParamsSerializer(
            data={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "waba_id": "123",
            }
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
