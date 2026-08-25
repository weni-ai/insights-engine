from uuid import uuid4

from django.test import SimpleTestCase

from insights.metrics.vtex.enums import OrdersSumGranularity, WeekStartsOn
from insights.metrics.vtex.serializers import InternalVTEXOrdersSumRequestSerializer


class TestInternalVTEXOrdersSumRequestSerializer(SimpleTestCase):
    def _payload(self, **overrides) -> dict:
        data = {
            "end_date": "2026-08-30",
            "granularity": OrdersSumGranularity.DAY,
            "project_uuid": str(uuid4()),
            "start_date": "2026-08-01",
            "utm_source": "weniabandonedcart",
        }
        data.update(overrides)
        return data

    def test_defaults_week_starts_on_to_sunday(self):
        serializer = InternalVTEXOrdersSumRequestSerializer(data=self._payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["week_starts_on"],
            WeekStartsOn.SUNDAY,
        )

    def test_rejects_invalid_weekday(self):
        serializer = InternalVTEXOrdersSumRequestSerializer(
            data=self._payload(week_starts_on="notaday")
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("week_starts_on", serializer.errors)

    def test_rejects_invalid_granularity(self):
        serializer = InternalVTEXOrdersSumRequestSerializer(
            data=self._payload(granularity="month")
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("granularity", serializer.errors)
