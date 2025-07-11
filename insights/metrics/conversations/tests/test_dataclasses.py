from django.test import TestCase

from insights.metrics.conversations.dataclass import ConversationTotalsMetrics


class TestConversationTotalsMetrics(TestCase):
    def test_from_values(self):
        by_ai = 150
        by_human = 50

        metrics = ConversationTotalsMetrics.from_values(by_ai, by_human)

        self.assertEqual(metrics.total, by_ai + by_human)
        self.assertEqual(metrics.by_ai.value, by_ai)
        self.assertEqual(metrics.by_ai.percentage, (by_ai / (by_ai + by_human)) * 100)
        self.assertEqual(metrics.by_human.value, by_human)
        self.assertEqual(
            metrics.by_human.percentage, (by_human / (by_ai + by_human)) * 100
        )

    def test_from_values_with_zero_values(self):
        by_ai = 0
        by_human = 0

        metrics = ConversationTotalsMetrics.from_values(by_ai, by_human)

        self.assertEqual(metrics.total, by_ai + by_human)
        self.assertEqual(metrics.by_ai.value, by_ai)
        self.assertEqual(metrics.by_ai.percentage, 0.0)
        self.assertEqual(metrics.by_human.value, by_human)
        self.assertEqual(metrics.by_human.percentage, 0.0)
