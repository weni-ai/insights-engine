from datetime import date
from django.test import TestCase

from insights.metrics.skills.exceptions import InvalidDateFormat
from insights.metrics.skills.validators import validate_date_str


class TestDateStringValidator(TestCase):
    def test_valid_date_str(self):
        date_str = "2023-01-01"
        result = validate_date_str(date_str)
        self.assertEqual(result, date(2023, 1, 1))

    def test_invalid_date_str(self):
        date_str = "2023-13-01"

        with self.assertRaises(InvalidDateFormat):
            validate_date_str(date_str)
