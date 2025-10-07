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

    def test_average_ticket_negative_count(self):
        """
        Test the average ticket calculation with negative total orders count.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=-5,  # Negative count
            total_orders_value=10000,
            currency_code="BRL",
        )

        # Negative count is treated as zero, so average_ticket should be 0
        self.assertEqual(metrics.average_ticket, 0)

    def test_average_ticket_edge_case_rounding_half_to_even(self):
        """
        Test the average ticket calculation with value that rounds to exactly 0.5.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=2,
            total_orders_value=1,  # 1 / 2 = 0.5
            currency_code="BRL",
        )

        # 1 / 2 = 0.5, Python's round() uses "round half to even" so 0.5 rounds to 0
        self.assertEqual(metrics.average_ticket, 0)

    def test_average_ticket_edge_case_rounding_half_down(self):
        """
        Test the average ticket calculation with value that rounds to exactly 0.5.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=2,
            total_orders_value=3,  # 3 / 2 = 1.5
            currency_code="BRL",
        )

        # 3 / 2 = 1.5, should round to 2
        self.assertEqual(metrics.average_ticket, 2)

    def test_average_ticket_very_small_values(self):
        """
        Test the average ticket calculation with very small values that round to zero.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=3,
            total_orders_value=1,  # 1 / 3 = 0.333... should round to 0
            currency_code="BRL",
        )

        # 1 / 3 = 0.333..., should round to 0
        self.assertEqual(metrics.average_ticket, 0)

    def test_average_ticket_very_small_values_rounds_up(self):
        """
        Test the average ticket calculation with very small values that round up to 1.
        """
        metrics = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=3,
            total_orders_value=2,  # 2 / 3 = 0.666... should round to 1
            currency_code="BRL",
        )

        # 2 / 3 = 0.666..., should round to 1
        self.assertEqual(metrics.average_ticket, 1)

    def test_average_ticket_large_values(self):
        """
        Test the average ticket calculation with large values.
        """
        metrics = SalesFunnelMetrics(
            leads_count=1000000,
            total_orders_count=1000,
            total_orders_value=999999999,  # Large value in cents
            currency_code="BRL",
        )

        # 999999999 / 1000 = 999999.999, should round to 1000000
        self.assertEqual(metrics.average_ticket, 1000000)
