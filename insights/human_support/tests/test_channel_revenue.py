from django.test import SimpleTestCase

from insights.human_support.channel_revenue import (
    ChannelRevenueSaleData,
    NullChannelRevenueSaleSource,
    calculate_share_percentage,
)
from insights.sources.channels.enums import Channel


class TestNullChannelRevenueSaleSource(SimpleTestCase):
    def test_returns_empty_channel_list(self):
        result = NullChannelRevenueSaleSource().get_channel_revenue_sale(
            {"project": "project-uuid"}
        )

        self.assertEqual(
            result,
            ChannelRevenueSaleData(metric="sale", currency_code="", rows=[]),
        )

    def test_echoes_revenue_metric(self):
        result = NullChannelRevenueSaleSource().get_channel_revenue_sale(
            {"metric": "revenue"}
        )

        self.assertEqual(result.metric, "revenue")
        self.assertEqual(result.rows, [])


class TestCalculateSharePercentage(SimpleTestCase):
    def test_returns_zero_without_total(self):
        self.assertEqual(calculate_share_percentage(0, 0), 0.0)
        self.assertEqual(calculate_share_percentage(0, 620), 0.0)

    def test_returns_share_from_the_design(self):
        self.assertEqual(calculate_share_percentage(2850, 620), 21.75)
        self.assertEqual(calculate_share_percentage(2850, 330), 11.58)

    def test_others_is_a_channel(self):
        self.assertEqual(Channel.OTHERS, "others")
