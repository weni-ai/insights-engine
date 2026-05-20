from datetime import date, datetime
from unittest.mock import patch

from django.test import TestCase

from insights.sources.dl_events.clients import (
    DataLakeEventsClient,
    _normalize_query_kwargs,
)


class NormalizeQueryKwargsTestCase(TestCase):
    def test_datetime_value_is_converted_to_isoformat(self):
        kwargs = {"date_start": datetime(2026, 5, 1, 0, 0, 0)}

        normalized = _normalize_query_kwargs(kwargs)

        self.assertEqual(normalized["date_start"], "2026-05-01T00:00:00")
        self.assertNotIn(" ", normalized["date_start"])

    def test_date_value_is_converted_to_isoformat(self):
        kwargs = {"date_start": date(2026, 5, 1)}

        normalized = _normalize_query_kwargs(kwargs)

        self.assertEqual(normalized["date_start"], "2026-05-01")

    def test_non_datetime_values_are_passed_through_unchanged(self):
        kwargs = {
            "event_name": "weni_nexus_data",
            "project": "fake-uuid",
            "key": "conversation_classification",
            "limit": 100,
            "metadata": None,
        }

        normalized = _normalize_query_kwargs(kwargs)

        self.assertEqual(normalized, kwargs)

    def test_mixed_kwargs_only_convert_datetime_values(self):
        kwargs = {
            "project": "fake-uuid",
            "date_start": datetime(2026, 5, 1, 0, 0, 0),
            "date_end": datetime(2026, 5, 19, 23, 59, 59),
            "limit": 100,
        }

        normalized = _normalize_query_kwargs(kwargs)

        self.assertEqual(normalized["project"], "fake-uuid")
        self.assertEqual(normalized["date_start"], "2026-05-01T00:00:00")
        self.assertEqual(normalized["date_end"], "2026-05-19T23:59:59")
        self.assertEqual(normalized["limit"], 100)


class DataLakeEventsClientTestCase(TestCase):
    """
    Tests that every DataLakeEventsClient method converts datetime/date
    query kwargs to ISO 8601 strings before forwarding them to the SDK.
    """

    def setUp(self):
        self.client = DataLakeEventsClient()
        self.project = "fake-project-uuid"
        self.start = datetime(2026, 5, 1, 0, 0, 0)
        self.end = datetime(2026, 5, 19, 23, 59, 59)
        self.start_iso = "2026-05-01T00:00:00"
        self.end_iso = "2026-05-19T23:59:59"

    def _assert_dates_were_normalized(self, mock_sdk):
        kwargs = mock_sdk.call_args.kwargs
        self.assertEqual(kwargs["date_start"], self.start_iso)
        self.assertEqual(kwargs["date_end"], self.end_iso)
        self.assertNotIn(" ", kwargs["date_start"])
        self.assertNotIn(" ", kwargs["date_end"])

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events")
    def test_get_events_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"id": 1}]

        self.client.get_events(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
            key="conversation_classification",
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_count")
    def test_get_events_count_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"count": 1}]

        self.client.get_events_count(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
            key="conversation_classification",
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_count_by_group")
    def test_get_events_count_by_group_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"payload_value": "1", "count": 1}]

        self.client.get_events_count_by_group(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
            key="conversation_classification",
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.get_events_sum")
    def test_get_events_sum_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"total": 100.0}]

        self.client.get_events_sum(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.get_events_avg")
    def test_get_events_avg_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"average": 10.0}]

        self.client.get_events_avg(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.get_events_max")
    def test_get_events_max_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"max_value": 50.0}]

        self.client.get_events_max(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.get_events_min")
    def test_get_events_min_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = [{"min_value": 1.0}]

        self.client.get_events_min(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_unique_contact_urns")
    def test_get_unique_contacts_count_converts_datetime_to_isoformat(self, mock_sdk):
        mock_sdk.return_value = 0

        self.client.get_unique_contacts_count(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_recurring_contact_urns")
    def test_get_returning_contacts_count_converts_datetime_to_isoformat(
        self, mock_sdk
    ):
        mock_sdk.return_value = 0

        self.client.get_returning_contacts_count(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_sdk.assert_called_once()
        self._assert_dates_were_normalized(mock_sdk)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_count")
    def test_get_events_count_accepts_date_value(self, mock_sdk):
        mock_sdk.return_value = [{"count": 1}]

        self.client.get_events_count(
            project=self.project,
            date_start=date(2026, 5, 1),
            date_end=date(2026, 5, 19),
        )

        kwargs = mock_sdk.call_args.kwargs
        self.assertEqual(kwargs["date_start"], "2026-05-01")
        self.assertEqual(kwargs["date_end"], "2026-05-19")

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_count")
    def test_get_events_count_passes_strings_through_unchanged(self, mock_sdk):
        mock_sdk.return_value = [{"count": 1}]

        self.client.get_events_count(
            event_name="weni_nexus_data",
            project=self.project,
            date_start=self.start_iso,
            date_end=self.end_iso,
            key="conversation_classification",
        )

        kwargs = mock_sdk.call_args.kwargs
        self.assertEqual(kwargs["date_start"], self.start_iso)
        self.assertEqual(kwargs["date_end"], self.end_iso)
        self.assertEqual(kwargs["event_name"], "weni_nexus_data")
        self.assertEqual(kwargs["project"], self.project)
        self.assertEqual(kwargs["key"], "conversation_classification")


class DataLakeEventsClientSilverTablesTestCase(TestCase):
    """
    Tests that the silver-tables branch in each method also normalizes
    datetime kwargs and still forwards the `table` argument.
    """

    def setUp(self):
        self.client = DataLakeEventsClient()
        self.project = "fake-project-uuid"
        self.table = "conversation_classification"
        self.start = datetime(2026, 5, 1, 0, 0, 0)
        self.end = datetime(2026, 5, 19, 23, 59, 59)
        self.start_iso = "2026-05-01T00:00:00"
        self.end_iso = "2026-05-19T23:59:59"

    def _assert_normalized_with_table(self, mock_sdk):
        kwargs = mock_sdk.call_args.kwargs
        self.assertEqual(kwargs["date_start"], self.start_iso)
        self.assertEqual(kwargs["date_end"], self.end_iso)
        self.assertEqual(kwargs["table"], self.table)
        self.assertNotIn(" ", kwargs["date_start"])
        self.assertNotIn(" ", kwargs["date_end"])

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", True)
    @patch("insights.sources.dl_events.clients.get_events_silver")
    def test_get_events_silver_branch_normalizes_datetime(self, mock_silver):
        mock_silver.return_value = [{"id": 1}]

        self.client.get_events(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_silver.assert_called_once()
        self._assert_normalized_with_table(mock_silver)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", True)
    @patch("insights.sources.dl_events.clients.get_events_silver_count")
    def test_get_events_count_silver_branch_normalizes_datetime(self, mock_silver):
        mock_silver.return_value = [{"count": 1}]

        self.client.get_events_count(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_silver.assert_called_once()
        self._assert_normalized_with_table(mock_silver)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", True)
    @patch("insights.sources.dl_events.clients.get_events_silver_count_by_group")
    def test_get_events_count_by_group_silver_branch_normalizes_datetime(
        self, mock_silver
    ):
        mock_silver.return_value = [{"payload_value": "1", "count": 1}]

        self.client.get_events_count_by_group(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_silver.assert_called_once()
        self._assert_normalized_with_table(mock_silver)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", True)
    @patch("insights.sources.dl_events.clients.get_events_silver_unique_contact_urns")
    def test_get_unique_contacts_count_silver_branch_normalizes_datetime(
        self, mock_silver
    ):
        mock_silver.return_value = 0

        self.client.get_unique_contacts_count(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_silver.assert_called_once()
        self._assert_normalized_with_table(mock_silver)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", True)
    @patch(
        "insights.sources.dl_events.clients.get_events_silver_recurring_contact_urns"
    )
    def test_get_returning_contacts_count_silver_branch_normalizes_datetime(
        self, mock_silver
    ):
        mock_silver.return_value = 0

        self.client.get_returning_contacts_count(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_silver.assert_called_once()
        self._assert_normalized_with_table(mock_silver)

    @patch("insights.sources.dl_events.clients.USE_SILVER_TABLES", False)
    @patch("insights.sources.dl_events.clients.get_events_silver_count")
    @patch("insights.sources.dl_events.clients.get_events_count")
    def test_silver_flag_off_uses_non_silver_method(self, mock_non_silver, mock_silver):
        mock_non_silver.return_value = [{"count": 1}]

        self.client.get_events_count(
            table=self.table,
            project=self.project,
            date_start=self.start,
            date_end=self.end,
        )

        mock_non_silver.assert_called_once()
        mock_silver.assert_not_called()
        kwargs = mock_non_silver.call_args.kwargs
        self.assertEqual(kwargs["date_start"], self.start_iso)
        self.assertEqual(kwargs["date_end"], self.end_iso)
        self.assertNotIn("table", kwargs)
