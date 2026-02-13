from insights.metrics.meta.typing import PricingDataPoint


class ConversationsByCategoryAggregations:
    def aggregate_volume_by_category(self, data: list[PricingDataPoint]) -> dict:
        categories = {}

        for item in data:
            category_name = item.get("pricing_category")
            count = item.get("volume")

            if category_name not in categories:
                categories[category_name] = 0

            categories[category_name] += count

        return categories
