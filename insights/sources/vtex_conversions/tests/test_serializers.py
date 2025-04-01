from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import serializers

from insights.metrics.meta.validators import MAX_ANALYTICS_DAYS_PERIOD_FILTER
from insights.sources.vtex_conversions.usecases.serializers import (
    OrdersConversionsFiltersSerializer,
)


class TestOrdersConversionsFiltersSerializer(TestCase):
    def test_cannot_get_metrics_with_dates_out_of_range(self):
        filters = {
            "waba_id": "123",
            "template_id": "456",
            "date_start": (
                timezone.now() - timedelta(days=MAX_ANALYTICS_DAYS_PERIOD_FILTER + 1)
            ).strftime("%Y-%m-%d"),
            "date_end": (timezone.now()).strftime("%Y-%m-%d"),
        }

        with self.assertRaises(serializers.ValidationError) as context:
            serializer = OrdersConversionsFiltersSerializer(data=filters)
            serializer.is_valid(raise_exception=True)

        self.assertIn("date_start", context.exception.detail)
        self.assertEqual(context.exception.detail["date_start"][0].code, "invalid")

    def test_cannot_get_metrics_with_end_date_before_start_date(self):
        filters = {
            "waba_id": "123",
            "template_id": "456",
            "date_start": (timezone.now()).strftime("%Y-%m-%d"),
            "date_end": (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        }

        with self.assertRaises(serializers.ValidationError) as context:
            serializer = OrdersConversionsFiltersSerializer(data=filters)
            serializer.is_valid(raise_exception=True)

        self.assertIn("date_end", context.exception.detail)
        self.assertEqual(
            context.exception.detail["date_end"][0].code, "end_date_before_start_date"
        )
