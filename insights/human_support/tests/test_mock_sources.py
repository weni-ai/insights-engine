from django.test import SimpleTestCase, TestCase

from insights.human_support.channel_revenue import ChannelRevenueSaleRow
from insights.human_support.mock.service import (
    mocked_human_support_dashboard_service,
    to_per_channel_results,
    to_per_representative_results,
    to_purchases_made_payload,
    to_sales_data_payload,
)
from insights.human_support.mock.sources import (
    CHANNEL_SALE_ROWS,
    CURRENT_AVERAGE_ORDER_VALUE,
    CURRENT_REVENUE,
    MockAverageOrderValueSource,
    MockChannelRevenueSaleSource,
    MockRepresentativePerformanceSource,
    MockRevenueSource,
    MockSalesFunnelSource,
    PREVIOUS_AVERAGE_ORDER_VALUE,
    PREVIOUS_REVENUE,
    SALES_FUNNEL,
)
from insights.human_support.sales_funnel import SalesFunnelData
from insights.projects.models import Project
from insights.sources.channels.enums import Channel


class TestMockRevenueSource(SimpleTestCase):
    def test_returns_current_then_previous_period(self):
        source = MockRevenueSource()

        self.assertEqual(source.get_revenue({}), CURRENT_REVENUE)
        self.assertEqual(source.get_revenue({}), PREVIOUS_REVENUE)


class TestMockAverageOrderValueSource(SimpleTestCase):
    def test_returns_current_then_previous_period(self):
        source = MockAverageOrderValueSource()

        self.assertEqual(source.get_average_order_value({}), CURRENT_AVERAGE_ORDER_VALUE)
        self.assertEqual(
            source.get_average_order_value({}), PREVIOUS_AVERAGE_ORDER_VALUE
        )


class TestMockSalesFunnelSource(SimpleTestCase):
    def test_returns_design_funnel(self):
        result = MockSalesFunnelSource().get_sales_funnel({})

        self.assertEqual(
            result, SalesFunnelData(leads_count=45000, purchases_count=4250)
        )


class TestMockChannelRevenueSaleSource(SimpleTestCase):
    def test_returns_sale_rows_by_default(self):
        result = MockChannelRevenueSaleSource().get_channel_revenue_sale({})

        self.assertEqual(result.metric, "sale")
        self.assertEqual(result.rows, CHANNEL_SALE_ROWS)

    def test_returns_revenue_rows_when_metric_is_revenue(self):
        result = MockChannelRevenueSaleSource().get_channel_revenue_sale(
            {"metric": "revenue"}
        )

        self.assertEqual(result.metric, "revenue")
        self.assertEqual(result.currency_code, "USD")
        self.assertEqual(
            result.rows[0],
            ChannelRevenueSaleRow(channel="whatsapp", value=176800.0),
        )

    def test_filters_by_channel(self):
        result = MockChannelRevenueSaleSource().get_channel_revenue_sale(
            {"channels": [Channel.WHATSAPP, Channel.OTHERS]}
        )

        self.assertEqual(
            [row.channel for row in result.rows],
            [Channel.WHATSAPP, Channel.OTHERS],
        )


class TestMockRepresentativePerformanceSource(SimpleTestCase):
    def test_filters_by_agent_email(self):
        source = MockRepresentativePerformanceSource()

        result = source.get_performance_by_representative({"agent": "emma@example.com"})

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].representative, "Emma Wilson")


class TestAssistedSalesMockPayloads(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )
        self.service = mocked_human_support_dashboard_service(self.project)

    def test_sales_data_matches_aligned_contract(self):
        payload = to_sales_data_payload(self.service, {})

        self.assertEqual(payload["average_order_value"], 284.0)
        self.assertEqual(payload["total_revenue"]["value"], 428450.0)
        self.assertEqual(payload["total_revenue"]["last_period_value"], 362480.0)
        self.assertEqual(payload["total_revenue"]["variation"], 18.2)

    def test_purchases_made_matches_aligned_contract(self):
        payload = to_purchases_made_payload(
            mocked_human_support_dashboard_service(self.project), {}
        )

        self.assertEqual(
            payload,
            {
                "leads_captured": {"value": 45000, "percentage": 100.0},
                "purchases_made": {"value": 4250, "percentage": 9.44},
            },
        )

    def test_per_channel_renames_fields(self):
        results = to_per_channel_results(
            mocked_human_support_dashboard_service(self.project),
            {"metric": "sale"},
        )

        self.assertEqual(results[0]["channel_name"], "whatsapp")
        self.assertEqual(results[0]["total_value"], 620)
        self.assertEqual(results[0]["percentage"], 21.75)

    def test_per_representative_uses_aligned_row_shape(self):
        results = to_per_representative_results(
            mocked_human_support_dashboard_service(self.project), {}
        )

        emma = results[0]
        self.assertEqual(
            emma["representative"],
            {"name": "Emma Wilson", "email": "emma@example.com"},
        )
        self.assertEqual(emma["conversions"], 41.5)
        self.assertEqual(emma["trend"]["variation_type"], "INCREASE")
        self.assertGreater(emma["trend"]["value"], 0)

        daniel = results[-1]
        self.assertEqual(daniel["trend"]["variation_type"], "DECREASE")
