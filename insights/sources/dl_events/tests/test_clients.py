from unittest.mock import patch

from django.test import TestCase

from insights.sources.dl_events.clients import DataLakeEventsClient


MODULE = "insights.sources.dl_events.clients"


class TestDataLakeEventsClientGetEvents(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid", "event_name": "test_event"}
        self.expected = [{"event": "data"}]

    @patch(f"{MODULE}.get_events_silver")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_silver_when_table_provided_and_setting_enabled(self, mock_silver):
        mock_silver.return_value = self.expected
        result = self.client.get_events(table="silver_table", **self.query_kwargs)

        mock_silver.assert_called_once_with(table="silver_table", **self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_bronze_when_table_is_none_and_setting_enabled(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events(table=None, **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_table_provided_but_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events(table="silver_table", **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_table_is_none_and_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events(**self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_silver", side_effect=ValueError("sdk error"))
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_propagates_exception_from_silver(self, mock_silver):
        with self.assertRaises(ValueError, msg="sdk error"):
            self.client.get_events(table="t", **self.query_kwargs)


class TestDataLakeEventsClientGetEventsCount(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid"}
        self.expected = [{"count": 42}]

    @patch(f"{MODULE}.get_events_silver_count")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_silver_when_table_provided_and_setting_enabled(self, mock_silver):
        mock_silver.return_value = self.expected
        result = self.client.get_events_count(table="silver_table", **self.query_kwargs)

        mock_silver.assert_called_once_with(table="silver_table", **self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_count")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_bronze_when_table_is_none(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events_count(table=None, **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_count")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events_count(table="silver_table", **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_silver_count", side_effect=RuntimeError("fail"))
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_propagates_exception(self, mock_silver):
        with self.assertRaises(RuntimeError):
            self.client.get_events_count(table="t", **self.query_kwargs)


class TestDataLakeEventsClientGetEventsCountByGroup(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid", "group_by": "status"}
        self.expected = [{"status": "open", "count": 5}]

    @patch(f"{MODULE}.get_events_silver_count_by_group")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_silver_when_table_provided_and_setting_enabled(self, mock_silver):
        mock_silver.return_value = self.expected
        result = self.client.get_events_count_by_group(
            table="silver_table", **self.query_kwargs
        )

        mock_silver.assert_called_once_with(table="silver_table", **self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_count_by_group")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_bronze_when_table_is_none(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events_count_by_group(table=None, **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(f"{MODULE}.get_events_count_by_group")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = self.expected
        result = self.client.get_events_count_by_group(
            table="silver_table", **self.query_kwargs
        )

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, self.expected)

    @patch(
        f"{MODULE}.get_events_silver_count_by_group",
        side_effect=RuntimeError("fail"),
    )
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_propagates_exception(self, mock_silver):
        with self.assertRaises(RuntimeError):
            self.client.get_events_count_by_group(table="t", **self.query_kwargs)


class TestDataLakeEventsClientSimpleDelegates(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid", "field": "duration"}

    @patch(f"{MODULE}.get_events_sum")
    def test_get_events_sum(self, mock_fn):
        mock_fn.return_value = [{"total": 100.0}]
        result = self.client.get_events_sum(**self.query_kwargs)

        mock_fn.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, [{"total": 100.0}])

    @patch(f"{MODULE}.get_events_avg")
    def test_get_events_avg(self, mock_fn):
        mock_fn.return_value = [{"average": 10.0}]
        result = self.client.get_events_avg(**self.query_kwargs)

        mock_fn.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, [{"average": 10.0}])

    @patch(f"{MODULE}.get_events_max")
    def test_get_events_max(self, mock_fn):
        mock_fn.return_value = [{"max_value": 50.0}]
        result = self.client.get_events_max(**self.query_kwargs)

        mock_fn.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, [{"max_value": 50.0}])

    @patch(f"{MODULE}.get_events_min")
    def test_get_events_min(self, mock_fn):
        mock_fn.return_value = [{"min_value": 1.0}]
        result = self.client.get_events_min(**self.query_kwargs)

        mock_fn.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, [{"min_value": 1.0}])


class TestDataLakeEventsClientGetUniqueContactsCount(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid"}

    @patch(f"{MODULE}.get_events_silver_unique_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_silver_when_table_provided_and_setting_enabled(self, mock_silver):
        mock_silver.return_value = 15
        result = self.client.get_unique_contacts_count(
            table="silver_table", **self.query_kwargs
        )

        mock_silver.assert_called_once_with(table="silver_table", **self.query_kwargs)
        self.assertEqual(result, 15)

    @patch(f"{MODULE}.get_events_unique_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_bronze_when_table_is_none(self, mock_bronze):
        mock_bronze.return_value = 10
        result = self.client.get_unique_contacts_count(table=None, **self.query_kwargs)

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, 10)

    @patch(f"{MODULE}.get_events_unique_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = 10
        result = self.client.get_unique_contacts_count(
            table="silver_table", **self.query_kwargs
        )

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, 10)

    @patch(
        f"{MODULE}.get_events_silver_unique_contact_urns",
        side_effect=RuntimeError("fail"),
    )
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_propagates_exception(self, mock_silver):
        with self.assertRaises(RuntimeError):
            self.client.get_unique_contacts_count(table="t", **self.query_kwargs)


class TestDataLakeEventsClientGetReturningContactsCount(TestCase):
    def setUp(self):
        self.client = DataLakeEventsClient()
        self.query_kwargs = {"project": "proj-uuid"}

    @patch(f"{MODULE}.get_events_silver_recurring_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_silver_when_table_provided_and_setting_enabled(self, mock_silver):
        mock_silver.return_value = 7
        result = self.client.get_returning_contacts_count(
            table="silver_table", **self.query_kwargs
        )

        mock_silver.assert_called_once_with(table="silver_table", **self.query_kwargs)
        self.assertEqual(result, 7)

    @patch(f"{MODULE}.get_events_recurring_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_uses_bronze_when_table_is_none(self, mock_bronze):
        mock_bronze.return_value = 3
        result = self.client.get_returning_contacts_count(
            table=None, **self.query_kwargs
        )

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, 3)

    @patch(f"{MODULE}.get_events_recurring_contact_urns")
    @patch(f"{MODULE}.USE_SILVER_TABLES", False)
    def test_uses_bronze_when_setting_disabled(self, mock_bronze):
        mock_bronze.return_value = 3
        result = self.client.get_returning_contacts_count(
            table="silver_table", **self.query_kwargs
        )

        mock_bronze.assert_called_once_with(**self.query_kwargs)
        self.assertEqual(result, 3)

    @patch(
        f"{MODULE}.get_events_silver_recurring_contact_urns",
        side_effect=RuntimeError("fail"),
    )
    @patch(f"{MODULE}.USE_SILVER_TABLES", True)
    def test_propagates_exception(self, mock_silver):
        with self.assertRaises(RuntimeError):
            self.client.get_returning_contacts_count(table="t", **self.query_kwargs)
