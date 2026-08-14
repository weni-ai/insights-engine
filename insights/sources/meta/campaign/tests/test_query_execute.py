from django.test import TestCase

from insights.sources.meta.campaign.clients import (
    MOCK_CAMPAIGNS,
    FlowsCampaignClient,
)
from insights.sources.meta.campaign.usecases.query_execute import QueryExecutor


class TestFlowsCampaignClient(TestCase):
    def setUp(self):
        self.client = FlowsCampaignClient(project_uuid="123e4567-e89b-12d3-a456-426614174000")

    def test_list_campaigns_returns_all_when_search_is_empty(self):
        data = self.client.list_campaigns()

        self.assertEqual(data["count"], len(MOCK_CAMPAIGNS))
        self.assertEqual(data["results"], MOCK_CAMPAIGNS)

    def test_list_campaigns_filters_by_name(self):
        data = self.client.list_campaigns(search="DIY")

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["name"], "Weekend DIY Deals")

    def test_list_campaigns_paginates_results(self):
        data = self.client.list_campaigns(page=2, page_size=2)

        self.assertEqual(data["count"], 5)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["name"], MOCK_CAMPAIGNS[2]["name"])


class TestMetaCampaignQueryExecutor(TestCase):
    def test_execute_passes_filters_to_client(self):
        data = QueryExecutor.execute(
            filters={
                "project": "123e4567-e89b-12d3-a456-426614174000",
                "search": "pro",
                "page": 1,
                "page_size": 10,
            }
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["name"], "Pro Account Signup")
