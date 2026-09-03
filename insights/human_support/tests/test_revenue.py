from django.test import SimpleTestCase

from insights.human_support.revenue import (
    NullRevenueSource,
    RevenueData,
    calculate_increase_percentage,
)


class TestNullRevenueSource(SimpleTestCase):
    def test_returns_zeroed_revenue(self):
        result = NullRevenueSource().get_revenue({"project": "project-uuid"})

        self.assertEqual(result, RevenueData(total=0.0, currency_code=""))


class TestCalculateIncreasePercentage(SimpleTestCase):
    def test_returns_full_increase_without_past_value(self):
        self.assertEqual(calculate_increase_percentage(0, 1000), 100.0)

    def test_returns_zero_without_past_and_current_values(self):
        self.assertEqual(calculate_increase_percentage(0, 0), 0.0)

    def test_returns_positive_variation(self):
        self.assertEqual(calculate_increase_percentage(362480, 428450), 18.2)

    def test_returns_negative_variation(self):
        self.assertEqual(calculate_increase_percentage(200, 50), -75.0)
