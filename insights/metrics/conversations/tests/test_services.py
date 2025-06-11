from django.test import TestCase

from insights.metrics.conversations.services import ConversationsMetricsService


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()
