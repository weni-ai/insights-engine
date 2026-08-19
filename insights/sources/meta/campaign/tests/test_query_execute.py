from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from insights.sources.meta.campaign.clients import FlowsCampaignClient
from insights.sources.meta.campaign.usecases.query_execute import QueryExecutor


FLOWS_CAMPAIGNS_PAYLOAD = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": 167301,
            "org": 7753,
            "project_uuid": "cec2f6a2-885f-49ed-914d-329762aeb8e5",
            "source_id": "12345678901",
            "source_type": "ad",
            "source_url": "https://fb.me/AAAAA",
            "headline": "Our new product",
            "body": "This is a great product",
            "first_seen_at": "2026-08-18T19:13:35.758315-03:00",
            "last_seen_at": "2026-08-18T19:13:35.758315-03:00",
            "created_at": "2026-08-18T19:13:35.758315-03:00",
            "updated_at": "2026-08-18T19:13:35.758315-03:00",
        }
    ],
}


@override_settings(
    FLOWS_URL="https://flows.weni.ai",
    CTWA_CAMPAIGNS_AFTER="2026-08-19T00:00:00-03:00",
)
class TestFlowsCampaignClient(TestCase):
    def setUp(self):
        self.client = FlowsCampaignClient(
            project_uuid="cec2f6a2-885f-49ed-914d-329762aeb8e5"
        )

    @patch("insights.sources.meta.campaign.clients.requests.get")
    @patch.object(FlowsCampaignClient, "headers", {"Authorization": "Bearer token"})
    def test_list_campaigns_maps_headline_and_source_id(self, mock_get):
        response = MagicMock()
        response.json.return_value = FLOWS_CAMPAIGNS_PAYLOAD
        mock_get.return_value = response

        data = self.client.list_campaigns(search="product", page=1, page_size=10)

        mock_get.assert_called_once_with(
            url="https://flows.weni.ai/api/v2/internals/ctwa_referral_sources",
            headers={"Authorization": "Bearer token"},
            params={
                "project_uuid": "cec2f6a2-885f-49ed-914d-329762aeb8e5",
                "limit": 10,
                "offset": 0,
                "after": "2026-08-19T00:00:00-03:00",
                "search": "product",
            },
            timeout=60,
        )
        response.raise_for_status.assert_called_once()
        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"],
            [{"name": "Our new product", "uuid": "12345678901"}],
        )

    @patch("insights.sources.meta.campaign.clients.requests.get")
    @patch.object(FlowsCampaignClient, "headers", {"Authorization": "Bearer token"})
    def test_list_campaigns_uses_source_id_when_headline_is_empty(self, mock_get):
        payload = {
            "count": 1,
            "results": [
                {
                    "id": 1,
                    "source_id": "999",
                    "headline": None,
                }
            ],
        }
        response = MagicMock()
        response.json.return_value = payload
        mock_get.return_value = response

        data = self.client.list_campaigns()

        self.assertEqual(data["results"][0]["name"], "999")
        self.assertEqual(data["results"][0]["uuid"], "999")

    @patch("insights.sources.meta.campaign.clients.requests.get")
    @patch.object(FlowsCampaignClient, "headers", {"Authorization": "Bearer token"})
    def test_list_campaigns_converts_page_to_limit_offset(self, mock_get):
        response = MagicMock()
        response.json.return_value = {"count": 1229, "results": []}
        mock_get.return_value = response

        self.client.list_campaigns(page=2, page_size=10)

        self.assertEqual(
            mock_get.call_args.kwargs["params"]["limit"],
            10,
        )
        self.assertEqual(mock_get.call_args.kwargs["params"]["offset"], 10)
        self.assertEqual(
            mock_get.call_args.kwargs["params"]["after"],
            "2026-08-19T00:00:00-03:00",
        )


class TestMetaCampaignQueryExecutor(TestCase):
    @patch("insights.sources.meta.campaign.usecases.query_execute.FlowsCampaignClient")
    def test_execute_passes_filters_to_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.list_campaigns.return_value = {
            "count": 1,
            "results": [{"name": "Our new product", "uuid": "12345678901"}],
        }
        mock_client_class.return_value = mock_client

        data = QueryExecutor.execute(
            filters={
                "project": "cec2f6a2-885f-49ed-914d-329762aeb8e5",
                "search": "product",
                "page": 1,
                "page_size": 10,
            }
        )

        mock_client_class.assert_called_once_with(
            project_uuid="cec2f6a2-885f-49ed-914d-329762aeb8e5"
        )
        mock_client.list_campaigns.assert_called_once_with(
            search="product",
            page=1,
            page_size=10,
        )
        self.assertEqual(data["results"][0]["name"], "Our new product")
