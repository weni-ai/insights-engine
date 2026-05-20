from unittest.mock import patch, MagicMock

from django.test import TestCase

from insights.utils import format_to_iso_utc, get_token_flows_authentication


class TestFormatToIsoUtc(TestCase):
    def test_valid_date_start_of_day(self):
        result = format_to_iso_utc("2024-01-15")
        self.assertEqual(result, "2024-01-15T00:00:00Z")

    def test_valid_date_end_of_day(self):
        result = format_to_iso_utc("2024-01-15", end_of_day=True)
        self.assertEqual(result, "2024-01-15T23:59:58Z")

    def test_invalid_format_returns_none(self):
        result = format_to_iso_utc("15/01/2024")
        self.assertIsNone(result)

    def test_empty_string_returns_none(self):
        result = format_to_iso_utc("")
        self.assertIsNone(result)

    @patch("insights.utils.datetime")
    def test_unexpected_exception_returns_none(self, mock_datetime):
        mock_datetime.strptime.side_effect = RuntimeError("unexpected")
        result = format_to_iso_utc("2024-01-15")
        self.assertIsNone(result)


class TestGetTokenFlowsAuthentication(TestCase):
    @patch("insights.utils.FlowsInternalAuthentication")
    def test_returns_api_token(self, mock_auth_cls):
        mock_client = MagicMock()
        mock_auth_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_token": "test-token-123"}
        mock_client.get_flows_user_api_token.return_value = mock_response

        result = get_token_flows_authentication("project-uuid", "user@example.com")

        self.assertEqual(result, "test-token-123")
        mock_client.get_flows_user_api_token.assert_called_once_with(
            "project-uuid", "user@example.com"
        )

    @patch("insights.utils.FlowsInternalAuthentication")
    def test_returns_none_when_no_api_token_in_response(self, mock_auth_cls):
        mock_client = MagicMock()
        mock_auth_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.get_flows_user_api_token.return_value = mock_response

        result = get_token_flows_authentication("project-uuid", "user@example.com")

        self.assertIsNone(result)
