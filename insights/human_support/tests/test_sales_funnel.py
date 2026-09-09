from django.test import SimpleTestCase

from insights.human_support.sales_funnel import (
    NullSalesFunnelSource,
    SalesFunnelData,
    calculate_conversion_percentage,
)


class TestNullSalesFunnelSource(SimpleTestCase):
    def test_returns_zeroed_sales_funnel(self):
        result = NullSalesFunnelSource().get_sales_funnel({"project": "project-uuid"})

        self.assertEqual(result, SalesFunnelData(leads_count=0, purchases_count=0))


class TestCalculateConversionPercentage(SimpleTestCase):
    def test_returns_zero_without_leads(self):
        self.assertEqual(calculate_conversion_percentage(0, 0), 0.0)
        self.assertEqual(calculate_conversion_percentage(0, 10), 0.0)

    def test_returns_conversion_from_the_design(self):
        self.assertEqual(calculate_conversion_percentage(45000, 4250), 9.44)
