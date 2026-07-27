from datetime import date, datetime, timezone

from django.test import TestCase

from insights.metrics.vtex.date_utils import to_utc_range
from insights.projects.models import Project


class TestToUtcRange(TestCase):
    def test_converts_date_range_to_utc_using_project_timezone(self):
        project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )

        start, end = to_utc_range(
            date(2023, 9, 1),
            date(2023, 9, 4),
            project,
        )

        self.assertEqual(
            start,
            datetime(2023, 9, 1, 3, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime(2023, 9, 5, 2, 59, 59, tzinfo=timezone.utc),
        )

    def test_defaults_to_utc_when_project_timezone_is_empty(self):
        project = Project.objects.create(name="Test Project", timezone=None)

        start, end = to_utc_range(
            date(2023, 9, 1),
            date(2023, 9, 2),
            project,
        )

        self.assertEqual(
            start,
            datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime(2023, 9, 2, 23, 59, 59, tzinfo=timezone.utc),
        )
