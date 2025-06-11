from django.test import TestCase

from insights.metrics.conversations.dataclass import ConversationTotalsMetrics
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsSerializer,
)


class TestConversationTotalsMetricsSerializer(TestCase):
    def test_serializer(self):
        totals = ConversationTotalsMetrics.from_values(
            by_ai=150,
            by_human=50,
        )
        serializer = ConversationTotalsMetricsSerializer(totals)
        data = serializer.data

        self.assertEqual(data["total"], totals.total)
        self.assertEqual(data["by_ai"]["value"], totals.by_ai.value)
        self.assertEqual(data["by_ai"]["percentage"], totals.by_ai.percentage)
        self.assertEqual(data["by_human"]["value"], totals.by_human.value)
        self.assertEqual(data["by_human"]["percentage"], totals.by_human.percentage)
