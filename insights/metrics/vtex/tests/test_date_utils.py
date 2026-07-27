from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from django.test import TestCase

from insights.metrics.vtex.date_utils import END_OF_DAY_TIME, to_utc_range
from insights.projects.models import Project


class TestToUtcRange(TestCase):
    def test_converts_date_range_to_utc_using_project_timezone(self):
        project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )
        start_date = date(2023, 9, 1)
        end_date = date(2023, 9, 4)
        project_tz = ZoneInfo(project.timezone)

        start, end = to_utc_range(start_date, end_date, project)

        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(end.tzinfo, timezone.utc)
        self.assertEqual(start.astimezone(project_tz).date(), start_date)
        self.assertEqual(start.astimezone(project_tz).time(), time.min)
        self.assertEqual(end.astimezone(project_tz).date(), end_date)
        self.assertEqual(end.astimezone(project_tz).time(), END_OF_DAY_TIME)

    def test_defaults_to_utc_when_project_timezone_is_empty(self):
        project = Project.objects.create(name="Test Project", timezone=None)
        start_date = date(2023, 9, 1)
        end_date = date(2023, 9, 2)

        start, end = to_utc_range(start_date, end_date, project)

        self.assertEqual(
            start,
            datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime.combine(end_date, END_OF_DAY_TIME, tzinfo=timezone.utc),
        )
