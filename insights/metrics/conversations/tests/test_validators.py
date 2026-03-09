from datetime import datetime, time

import pytz
from django.test import TestCase
from rest_framework import serializers

from insights.metrics.conversations.validators import ConversationsDatesValidator
from insights.projects.models import Project


class TestConversationsDatesValidator(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def test_validate_start_date_after_end_date(self):
        """Raises ValidationError when start_date is after end_date."""
        start_date = datetime(2025, 3, 10)
        end_date = datetime(2025, 3, 5)
        validator = ConversationsDatesValidator(
            project=self.project,
            start_date=start_date,
            end_date=end_date,
        )
        with self.assertRaises(serializers.ValidationError) as ctx:
            validator.validate()
        self.assertEqual(
            str(ctx.exception.detail["start_date"]),
            "Start date must be before end date",
        )
        self.assertEqual(
            ctx.exception.get_codes(), {"start_date": "start_date_after_end_date"}
        )

    def test_validate_same_start_and_end_date_succeeds(self):
        """Accepts same date for start and end (single day range)."""
        same_date = datetime(2025, 3, 5)
        validator = ConversationsDatesValidator(
            project=self.project,
            start_date=same_date,
            end_date=same_date,
        )
        start, end = validator.validate()
        self.assertLessEqual(start, end)
        self.assertEqual(start.date(), same_date.date())
        self.assertEqual(end.date(), same_date.date())

    def test_validate_uses_utc_when_project_has_no_timezone(self):
        """Normalizes dates to UTC when project has no timezone."""
        self.project.timezone = None
        self.project.save()
        start_date = datetime(2025, 3, 5)
        end_date = datetime(2025, 3, 7)
        validator = ConversationsDatesValidator(
            project=self.project,
            start_date=start_date,
            end_date=end_date,
        )
        start, end = validator.validate()
        # Midnight and 23:59:59 in UTC for the given dates
        self.assertEqual(start, datetime(2025, 3, 5, 0, 0, 0))
        self.assertEqual(end, datetime(2025, 3, 7, 23, 59, 59))

    def test_validate_uses_project_timezone(self):
        """Normalizes start to 00:00:00 and end to 23:59:59 in project timezone, returned as naive UTC."""
        self.project.timezone = "America/Sao_Paulo"  # UTC-3
        self.project.save()
        start_date = datetime(2025, 3, 5)
        end_date = datetime(2025, 3, 6)
        validator = ConversationsDatesValidator(
            project=self.project,
            start_date=start_date,
            end_date=end_date,
        )
        start, end = validator.validate()
        tz = pytz.timezone("America/Sao_Paulo")
        # 2025-03-05 00:00:00 in São Paulo = 2025-03-05 03:00:00 UTC (no DST in March)
        expected_start = (
            tz.localize(datetime(2025, 3, 5, 0, 0, 0))
            .astimezone(pytz.UTC)
            .replace(tzinfo=None)
        )
        expected_end = (
            tz.localize(datetime(2025, 3, 6, 23, 59, 59))
            .astimezone(pytz.UTC)
            .replace(tzinfo=None)
        )
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

    def test_validate_returns_tuple_of_normalized_dates(self):
        """validate() returns (start_date, end_date) as normalized naive UTC datetimes."""
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 3, 10)
        validator = ConversationsDatesValidator(
            project=self.project,
            start_date=start_date,
            end_date=end_date,
        )
        result = validator.validate()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        start, end = result
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)
        self.assertIsNone(start.tzinfo)
        self.assertIsNone(end.tzinfo)
        self.assertEqual(start.time(), time.min)
        self.assertEqual(end.time(), time(23, 59, 59))
