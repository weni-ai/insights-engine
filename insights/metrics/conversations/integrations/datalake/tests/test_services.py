from datetime import datetime, timedelta
import json
import uuid
from unittest.mock import call, patch
from django.test import TestCase

from insights.metrics.conversations.dataclass import ConversationsTotalsMetrics
from insights.metrics.conversations.integrations.datalake.dataclass import (
    SalesFunnelData,
)
from insights.sources.dl_events.tests.mock_client import (
    ClassificationMockDataLakeEventsClient,
)
from insights.metrics.conversations.integrations.datalake.services import (
    DatalakeConversationsMetricsService,
)


class DatalakeConversationsMetricsServiceTestCase(TestCase):
    def setUp(self):
        self.service = DatalakeConversationsMetricsService(
            events_client=ClassificationMockDataLakeEventsClient()
        )

    def test_get_conversations_totals(self):
        results = self.service.get_conversations_totals(
            project_uuid=uuid.uuid4(),
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
        )

        self.assertIsInstance(results, ConversationsTotalsMetrics)

    def test_get_unclassified_label(self):
        label = self.service._get_unclassified_label("en")
        self.assertEqual(label, "Unclassified")

        label = self.service._get_unclassified_label("pt-br")
        self.assertEqual(label, "Não classificadas")

        label = self.service._get_unclassified_label("es")
        self.assertEqual(label, "No clasificadas")

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events_count"
    )
    def test_get_sales_funnel_data(
        self, mock_data_lake_events_count_client, mock_data_lake_events_client
    ):
        def get_events(**kwargs):
            if kwargs.get("offset") == 0:
                return [{"metadata": json.dumps({"currency": "BRL", "value": 100})}]

            return []

        mock_data_lake_events_client.side_effect = get_events
        mock_data_lake_events_count_client.return_value = [{"count": 10}]

        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        results = self.service.get_sales_funnel_data(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertIsInstance(results, SalesFunnelData)

        mock_data_lake_events_client.assert_has_calls(
            [
                call(
                    event_name="conversion_purchase",
                    project=project_uuid,
                    date_start=start_date,
                    date_end=end_date,
                    limit=5000,
                    offset=0,
                ),
                call(
                    event_name="conversion_purchase",
                    project=project_uuid,
                    date_start=start_date,
                    date_end=end_date,
                    limit=5000,
                    offset=5000,
                ),
            ]
        )

        self.assertEqual(results.leads_count, 10)
        self.assertEqual(results.total_orders_count, 1)
        self.assertEqual(results.total_orders_value, 10000)  # Converted to cents
        self.assertEqual(results.currency_code, "BRL")
