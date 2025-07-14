from datetime import datetime, timedelta
import uuid
from django.test import TestCase

from insights.metrics.conversations.integrations.datalake.dataclass import (
    DatalakeConversationsTotalsMetrics,
)
from insights.sources.dl_events.tests.mock_client import MockDataLakeEventsClient
from insights.metrics.conversations.integrations.datalake.services import (
    DatalakeConversationsMetricsService,
)


class DatalakeConversationsMetricsServiceTestCase(TestCase):
    def setUp(self):
        self.service = DatalakeConversationsMetricsService(
            events_client=MockDataLakeEventsClient()
        )

    def test_get_conversations_totals(self):
        results = self.service.get_conversations_totals(
            project=uuid.uuid4(),
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
        )

        self.assertIsInstance(results, DatalakeConversationsTotalsMetrics)
