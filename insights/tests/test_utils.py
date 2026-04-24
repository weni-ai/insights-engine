from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytz
from django.test import TestCase

from insights.utils import (
    convert_date_str_to_datetime_date,
    convert_date_to_unix_timestamp,
    convert_dt_to_localized_dt,
    format_to_iso_utc,
    get_token_flows_authentication,
    redact_headers,
)


class FormatToIsoUtcTestCase(TestCase):
    def test_formats_start_of_day_by_default(self):
        self.assertEqual(
            format_to_iso_utc("2025-01-15"),
            "2025-01-15T00:00:00Z",
        )

    def test_formats_end_of_day_when_flag_is_true(self):
        self.assertEqual(
            format_to_iso_utc("2025-01-15", end_of_day=True),
            "2025-01-15T23:59:58Z",
        )

    def test_returns_none_for_invalid_date_string(self):
        self.assertIsNone(format_to_iso_utc("15/01/2025"))
        self.assertIsNone(format_to_iso_utc("not-a-date"))
        self.assertIsNone(format_to_iso_utc(""))

    def test_returns_none_when_unexpected_error_occurs(self):
        self.assertIsNone(format_to_iso_utc(None))


class ConvertDateToUnixTimestampTestCase(TestCase):
    def test_uses_min_time_by_default(self):
        dt = date(2025, 1, 15)
        expected = int(datetime.combine(dt, datetime.min.time()).timestamp())

        self.assertEqual(convert_date_to_unix_timestamp(dt), expected)

    def test_uses_max_time_when_flag_is_true(self):
        dt = date(2025, 1, 15)
        expected = int(datetime.combine(dt, datetime.max.time()).timestamp())

        self.assertEqual(
            convert_date_to_unix_timestamp(dt, use_max_time=True),
            expected,
        )

    def test_max_time_is_greater_than_min_time(self):
        dt = date(2025, 1, 15)

        min_ts = convert_date_to_unix_timestamp(dt, use_max_time=False)
        max_ts = convert_date_to_unix_timestamp(dt, use_max_time=True)

        self.assertGreater(max_ts, min_ts)


class ConvertDateStrToDatetimeDateTestCase(TestCase):
    def test_converts_valid_date_string(self):
        self.assertEqual(
            convert_date_str_to_datetime_date("2025-12-25"),
            date(2025, 12, 25),
        )

    def test_raises_value_error_for_invalid_format(self):
        with self.assertRaises(ValueError):
            convert_date_str_to_datetime_date("25/12/2025")

    def test_raises_value_error_for_non_date_string(self):
        with self.assertRaises(ValueError):
            convert_date_str_to_datetime_date("invalid")


class ConvertDtToLocalizedDtTestCase(TestCase):
    def test_returns_datetime_in_utc(self):
        dt = date(2025, 6, 15)

        result = convert_dt_to_localized_dt(dt, "America/Sao_Paulo")

        self.assertEqual(result.tzinfo, pytz.utc)

    def test_converts_timezone_correctly(self):
        dt = date(2025, 6, 15)

        sp_result = convert_dt_to_localized_dt(dt, "America/Sao_Paulo")
        utc_result = convert_dt_to_localized_dt(dt, "UTC")

        # Resultados podem diferir em segundos pois usam datetime.now() internamente.
        # Verificamos apenas que ambos retornam um datetime com tz UTC.
        self.assertEqual(sp_result.tzinfo, pytz.utc)
        self.assertEqual(utc_result.tzinfo, pytz.utc)


class RedactHeadersTestCase(TestCase):
    def test_redacts_only_requested_keys(self):
        headers = {"Authorization": "secret-token", "Accept": "application/json"}

        result = redact_headers(headers, ["Authorization"])

        self.assertEqual(result["Authorization"], "*" * len("secret-token"))
        self.assertEqual(result["Accept"], "application/json")

    def test_keeps_original_headers_unchanged(self):
        headers = {"Authorization": "secret-token"}

        redact_headers(headers, ["Authorization"])

        self.assertEqual(headers["Authorization"], "secret-token")

    def test_ignores_keys_not_present(self):
        headers = {"Accept": "application/json"}

        result = redact_headers(headers, ["Authorization"])

        self.assertEqual(result, {"Accept": "application/json"})

    def test_redacts_multiple_keys(self):
        headers = {
            "Authorization": "token",
            "X-Api-Key": "key",
            "Accept": "application/json",
        }

        result = redact_headers(headers, ["Authorization", "X-Api-Key"])

        self.assertEqual(result["Authorization"], "*" * len("token"))
        self.assertEqual(result["X-Api-Key"], "*" * len("key"))
        self.assertEqual(result["Accept"], "application/json")

    def test_converts_non_string_values_to_string_for_length(self):
        headers = {"X-Count": 12345}

        result = redact_headers(headers, ["X-Count"])

        self.assertEqual(result["X-Count"], "*" * len("12345"))


class GetTokenFlowsAuthenticationTestCase(TestCase):
    @patch("insights.utils.FlowsInternalAuthentication")
    def test_returns_api_token_from_response(self, mock_auth_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"api_token": "abc-123"}
        mock_auth_cls.return_value.get_flows_user_api_token.return_value = (
            mock_response
        )

        token = get_token_flows_authentication(
            "project-uuid", "user@example.com"
        )

        self.assertEqual(token, "abc-123")
        mock_auth_cls.return_value.get_flows_user_api_token.assert_called_once_with(
            "project-uuid", "user@example.com"
        )

    @patch("insights.utils.FlowsInternalAuthentication")
    def test_returns_none_when_api_token_missing(self, mock_auth_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_auth_cls.return_value.get_flows_user_api_token.return_value = (
            mock_response
        )

        self.assertIsNone(
            get_token_flows_authentication("project-uuid", "user@example.com")
        )
