import uuid
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase

from insights.sources.custom_status.client import CustomStatusRESTClient


class TestCustomStatusRESTClient(TestCase):
    def setUp(self):
        self.project = MagicMock()
        self.project.uuid = uuid.uuid4()

        with patch.object(CustomStatusRESTClient, "get_module_token", return_value="Bearer fake"):
            self.client = CustomStatusRESTClient(project=self.project)

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"id": 1}]}
        mock_get.return_value = mock_response

        filters = {"created_on__gte": "2024-01-01", "created_on__lte": "2024-01-31"}
        result = self.client.list_custom_status(filters)

        self.assertEqual(result, {"results": [{"id": 1}]})
        call_kwargs = mock_get.call_args
        self.assertIn("start_date", call_kwargs.kwargs.get("params", {}))
        self.assertIn("end_date", call_kwargs.kwargs.get("params", {}))
        self.assertNotIn("created_on__gte", call_kwargs.kwargs.get("params", {}))

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status_without_date_filters(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = self.client.list_custom_status({"status": "open"})

        self.assertEqual(result, {"results": []})
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params", {})
        self.assertEqual(params, {"status": "open"})

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status_types(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"uuid": "abc-123", "name": "Type A", "extra": "ignored"},
                {"uuid": "def-456", "name": "Type B", "extra": "ignored"},
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.list_custom_status_types()

        self.assertEqual(
            result,
            [
                {"uuid": "abc-123", "name": "Type A"},
                {"uuid": "def-456", "name": "Type B"},
            ],
        )
        call_kwargs = mock_get.call_args
        self.assertEqual(
            call_kwargs.kwargs.get("params", {}),
            {"project": str(self.project.uuid)},
        )

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status_types_empty_results(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = self.client.list_custom_status_types()

        self.assertEqual(result, [])

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status_by_agent(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"agents": [{"name": "Agent 1"}]}
        mock_get.return_value = mock_response

        filters = {"created_on__gte": "2024-01-01", "created_on__lte": "2024-01-31"}
        result = self.client.list_custom_status_by_agent(filters)

        self.assertEqual(result, {"agents": [{"name": "Agent 1"}]})
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params", {})
        self.assertIn("start_date", params)
        self.assertIn("end_date", params)
        self.assertNotIn("created_on__gte", params)

    @patch("insights.sources.custom_status.client.requests.get")
    @patch.object(CustomStatusRESTClient, "headers", new_callable=PropertyMock, return_value={"Authorization": "Bearer fake"})
    def test_list_custom_status_by_agent_without_date_filters(self, mock_headers, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"agents": []}
        mock_get.return_value = mock_response

        result = self.client.list_custom_status_by_agent({"agent_id": "123"})

        self.assertEqual(result, {"agents": []})
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params", {})
        self.assertEqual(params, {"agent_id": "123"})
