from datetime import datetime
from django.test import TestCase

from insights.widgets.usecases.get_source_data import (
    set_live_day,
    apply_timezone_to_filters,
    format_date,
    convert_to_iso,
)


class TestDateFunctions(TestCase):
    def setUp(self):
        self.default_filters = {
            "created_at__gte": "today",
            "created_at__lte": "2024-03-20",
            "updated_at__gte": "2024-03-19",
            "updated_at__lte": "today",
        }

    def test_set_live_day(self):
        """Test that 'today' values are replaced with start of current day"""
        set_live_day(self.default_filters)

        # Check that 'today' values were replaced with datetime objects
        self.assertIsInstance(self.default_filters["created_at__gte"], datetime)
        self.assertIsInstance(self.default_filters["updated_at__lte"], datetime)

        # Check that the time is set to start of day (00:00:00)
        self.assertEqual(self.default_filters["created_at__gte"].hour, 0)
        self.assertEqual(self.default_filters["created_at__gte"].minute, 0)
        self.assertEqual(self.default_filters["created_at__gte"].second, 0)

        # Check that non-'today' values remain unchanged
        self.assertEqual(self.default_filters["created_at__lte"], "2024-03-20")
        self.assertEqual(self.default_filters["updated_at__gte"], "2024-03-19")

    def test_apply_timezone_to_filters(self):
        """Test that datetime values are properly localized to project timezone"""
        # First set some datetime values
        test_filters = {
            "created_at__gte": datetime(2024, 3, 20),
            "created_at__lte": ["2024-03-20"],
            "updated_at__gte": datetime(2024, 3, 19),
            "updated_at__lte": datetime(2024, 3, 20),
        }

        project_timezone_str = "America/Sao_Paulo"
        apply_timezone_to_filters(test_filters, project_timezone_str)

        # Check that datetime values are timezone-aware
        self.assertIsNotNone(test_filters["created_at__gte"].tzinfo)
        self.assertEqual(
            test_filters["created_at__gte"].tzinfo.zone, project_timezone_str
        )

        # Check that list values are properly converted
        self.assertIsInstance(test_filters["created_at__lte"], datetime)
        self.assertIsNotNone(test_filters["created_at__lte"].tzinfo)

        # Check that all datetime values have timezone
        for key, value in test_filters.items():
            if isinstance(value, datetime):
                self.assertIsNotNone(value.tzinfo)
                self.assertEqual(value.tzinfo.zone, project_timezone_str)

    def test_format_date(self):
        """Test that datetime values are properly formatted with start/end of day"""
        # Set up test data
        test_date = datetime(2024, 3, 20, 15, 30, 45)
        self.default_filters = {
            "created_at__gte": test_date,
            "created_at__lte": test_date,
        }

        format_date(self.default_filters)

        # Check that __gte dates are set to start of day
        self.assertEqual(self.default_filters["created_at__gte"].hour, 0)
        self.assertEqual(self.default_filters["created_at__gte"].minute, 0)
        self.assertEqual(self.default_filters["created_at__gte"].second, 0)
        self.assertEqual(self.default_filters["created_at__gte"].microsecond, 0)

        # Check that __lte dates are set to end of day
        self.assertEqual(self.default_filters["created_at__lte"].hour, 23)
        self.assertEqual(self.default_filters["created_at__lte"].minute, 59)
        self.assertEqual(self.default_filters["created_at__lte"].second, 59)
        self.assertEqual(self.default_filters["created_at__lte"].microsecond, 999999)

    def test_convert_to_iso(self):
        """Test that datetime values are converted to ISO format strings"""
        # Set up test data
        test_date = datetime(2024, 3, 20, 15, 30, 45)
        self.default_filters = {
            "created_at": test_date,
            "updated_at": "2024-03-20",  # Non-datetime value
        }

        convert_to_iso(self.default_filters)

        # Check that datetime was converted to ISO format string
        self.assertIsInstance(self.default_filters["created_at"], str)
        self.assertEqual(self.default_filters["created_at"], "2024-03-20T15:30:45")

        # Check that non-datetime values remain unchanged
        self.assertEqual(self.default_filters["updated_at"], "2024-03-20")
