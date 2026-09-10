from django.test import SimpleTestCase

from insights.human_support.performance import (
    NullRepresentativePerformanceSource,
    RepresentativePerformanceData,
    calculate_average_order_value,
)


class TestNullRepresentativePerformanceSource(SimpleTestCase):
    def test_returns_empty_table(self):
        result = (
            NullRepresentativePerformanceSource().get_performance_by_representative(
                {"project": "project-uuid"}
            )
        )

        self.assertEqual(result, RepresentativePerformanceData())


class TestCalculateAverageOrderValue(SimpleTestCase):
    def test_returns_zero_without_sales(self):
        self.assertEqual(calculate_average_order_value(1000, 0), 0.0)

    def test_returns_aov_from_the_design(self):
        self.assertEqual(calculate_average_order_value(72340, 254), 285.0)
        self.assertEqual(calculate_average_order_value(64120, 218), 294.0)
        self.assertEqual(calculate_average_order_value(58910, 176), 335.0)
        self.assertEqual(calculate_average_order_value(51470, 168), 306.0)
