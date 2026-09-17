from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from django.test import TestCase

from insights.metrics.vtex.date_utils import (
    END_OF_DAY_TIME,
    iter_period_keys,
    period_key_for,
    to_utc_range,
    week_start,
)
from insights.metrics.vtex.enums import OrdersSumGranularity, WeekStartsOn
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


class TestWeekStart(TestCase):
    def test_sunday_week_start_for_saturday(self):
        self.assertEqual(
            week_start(date(2026, 8, 1), WeekStartsOn.SUNDAY),
            date(2026, 7, 26),
        )

    def test_monday_week_start_for_saturday(self):
        self.assertEqual(
            week_start(date(2026, 8, 1), WeekStartsOn.MONDAY),
            date(2026, 7, 27),
        )

    def test_week_start_on_the_same_weekday_is_unchanged(self):
        self.assertEqual(
            week_start(date(2026, 7, 26), WeekStartsOn.SUNDAY),
            date(2026, 7, 26),
        )


class TestPeriodKeyFor(TestCase):
    def test_day_granularity_returns_the_same_date(self):
        self.assertEqual(
            period_key_for(
                date(2026, 8, 1),
                OrdersSumGranularity.DAY,
                WeekStartsOn.SUNDAY,
            ),
            date(2026, 8, 1),
        )

    def test_week_granularity_uses_week_start_before_the_date(self):
        self.assertEqual(
            period_key_for(
                date(2026, 8, 1),
                OrdersSumGranularity.WEEK,
                WeekStartsOn.SUNDAY,
            ),
            date(2026, 7, 26),
        )


class TestIterPeriodKeys(TestCase):
    def test_day_iteration_is_inclusive(self):
        keys = iter_period_keys(
            date(2026, 8, 1),
            date(2026, 8, 3),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )
        self.assertEqual(
            keys,
            [date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3)],
        )

    def test_week_iteration_includes_week_starting_before_start_date(self):
        keys = iter_period_keys(
            date(2026, 8, 1),
            date(2026, 8, 14),
            OrdersSumGranularity.WEEK,
            WeekStartsOn.SUNDAY,
        )
        self.assertEqual(
            keys,
            [date(2026, 7, 26), date(2026, 8, 2), date(2026, 8, 9)],
        )

    def test_zero_fill_key_list_covers_the_full_range(self):
        keys = iter_period_keys(
            date(2026, 8, 1),
            date(2026, 8, 30),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )
        self.assertEqual(keys[0], date(2026, 8, 1))
        self.assertEqual(keys[-1], date(2026, 8, 30))
        self.assertEqual(len(keys), 30)
