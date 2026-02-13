from django.test import TestCase

from insights.metrics.meta.aggregations import ConversationsByCategoryAggregations
from insights.metrics.meta.typing import PricingDataPoint


class TestConversationsByCategoryAggregations(TestCase):
    def test_aggregate_volume_by_category(self):
        data = [
            PricingDataPoint(
                start=1, end=2, pricing_category="category1", volume=10, cost=0
            ),
            PricingDataPoint(
                start=1, end=2, pricing_category="category1", volume=10, cost=0
            ),
            PricingDataPoint(
                start=1, end=2, pricing_category="category2", volume=20, cost=0
            ),
        ]
        result = ConversationsByCategoryAggregations().aggregate_volume_by_category(
            data
        )
        self.assertEqual(result, {"category1": 20, "category2": 20})
