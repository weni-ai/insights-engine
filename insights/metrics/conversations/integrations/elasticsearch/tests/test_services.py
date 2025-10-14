import uuid


from django.test import TestCase

from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.integrations.elasticsearch.tests.mock import (
    MockElasticsearchClient,
)


class TestConversationsElasticsearchService(TestCase):
    def setUp(self):
        self.service = ConversationsElasticsearchService(
            client=MockElasticsearchClient(),
        )

    def test_get_flowsrun_results_by_contacts(self):
        op_field = "user_feedback"

        # Configure the mock to return the expected data structure
        self.service.client.get.return_value = {
            "hits": {
                "total": {"value": 10},
                "hits": [
                    {
                        "_source": {
                            "project_uuid": uuid.uuid4(),
                            "contact_uuid": uuid.uuid4(),
                            "created_on": "2025-01-01",
                            "contact_name": "John Doe",
                            "contact_urn": "1234567890",
                            "modified_on": "2025-01-01",
                            "values": [
                                {
                                    "name": op_field,
                                    "value": "5",
                                }
                            ],
                        }
                    }
                ],
            }
        }

        results = self.service.get_flowsrun_results_by_contacts(
            project_uuid=uuid.uuid4(),
            flow_uuid=uuid.uuid4(),
            start_date="2025-01-01",
            end_date="2025-01-02",
            op_field=op_field,
            page_size=10,
            page_number=1,
        )

        self.assertIsInstance(results, dict)
        self.assertIn("pagination", results)
        self.assertIn("contacts", results)
        self.assertEqual(results["pagination"]["current_page"], 1)
        self.assertEqual(results["pagination"]["total_pages"], 1)
        self.assertEqual(results["pagination"]["page_size"], 10)
        self.assertEqual(results["pagination"]["total_items"], 10)
        self.assertEqual(len(results["contacts"]), 1)
        self.assertEqual(results["contacts"][0]["contact"]["name"], "John Doe")
        self.assertEqual(results["contacts"][0]["urn"], "1234567890")
        self.assertEqual(results["contacts"][0]["op_field_value"], "5")
        self.assertEqual(results["contacts"][0]["modified_on"], "2025-01-01")
