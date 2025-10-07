from django.test import TestCase

from insights.metrics.conversations.dataclass import SalesFunnelMetrics


class SalesFunnelMetricsTestCase(TestCase):
    """
    Test cases for SalesFunnelMetrics.
    """

    def test_average_ticket(self):
        """
        Test the average ticket calculation.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=10,
            total_orders_value=10000,
            currency_code="BRL",
        )

        self.assertEqual(metrics.average_ticket, 1000)

    def test_average_ticket_zero(self):
        """
        Test the average ticket calculation when total orders count is zero.
        """

        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=0,
            total_orders_value=0,
            currency_code="BRL",
        )

        self.assertEqual(metrics.average_ticket, 0)

    def test_average_ticket_with_odd_division_with_lower_rounding_result(self):
        """
        Test the average ticket calculation when total orders value is not divisible by total orders count.
        """

        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=3,
            total_orders_value=10000,
            currency_code="BRL",
        )

        # There is a loss here because of the rounding
        # as 10000 / 3 = 3333.333333333333
        self.assertEqual(metrics.average_ticket, 3333)

    def test_average_ticket_with_odd_division_with_higher_rounding_result(self):
        """
        Test the average ticket calculation when total orders value is not divisible by total orders count.
        """

        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=3,
            total_orders_value=10001,
            currency_code="BRL",
        )

        # There is a loss here because of the rounding
        # as 10001 / 3 = 3333.666666666666
        self.assertEqual(metrics.average_ticket, 3334)
