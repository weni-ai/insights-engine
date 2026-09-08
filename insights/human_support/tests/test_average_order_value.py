from django.test import SimpleTestCase

from insights.human_support.average_order_value import (
    AverageOrderValueData,
    NullAverageOrderValueSource,
)


class TestNullAverageOrderValueSource(SimpleTestCase):
    def test_returns_zeroed_average_order_value(self):
        result = NullAverageOrderValueSource().get_average_order_value(
            {"project": "project-uuid"}
        )

        self.assertEqual(result, AverageOrderValueData(value=0.0, currency_code=""))
