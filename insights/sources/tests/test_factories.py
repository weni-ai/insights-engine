from unittest.mock import patch

from django.test import TestCase

from insights.sources.base import BaseQueryExecutor
from insights.sources.factories import SourceQueryExecutorFactory


class TestSourceQueryExecutorFactory(TestCase):
    @patch("insights.sources.factories.import_string")
    def test_returns_executor_for_valid_source(self, mock_import_string):
        mock_executor = type("MockExecutor", (BaseQueryExecutor,), {
            "execute": classmethod(lambda cls, *a, **kw: None),
        })
        mock_import_string.return_value = mock_executor

        result = SourceQueryExecutorFactory.get_source_query_executor("rooms")

        self.assertEqual(result, mock_executor)
        mock_import_string.assert_called_once_with(
            "insights.sources.rooms.usecases.query_execute.QueryExecutor"
        )

    @patch("insights.sources.factories.import_string")
    def test_returns_none_for_nonexistent_source(self, mock_import_string):
        mock_import_string.side_effect = ModuleNotFoundError("No module")

        result = SourceQueryExecutorFactory.get_source_query_executor(
            "nonexistent_source"
        )

        self.assertIsNone(result)

    @patch("insights.sources.factories.import_string")
    def test_returns_none_on_import_error(self, mock_import_string):
        mock_import_string.side_effect = ImportError("Cannot import")

        result = SourceQueryExecutorFactory.get_source_query_executor("bad_source")

        self.assertIsNone(result)

    @patch("insights.sources.factories.import_string")
    def test_returns_none_on_attribute_error(self, mock_import_string):
        mock_import_string.side_effect = AttributeError("No attribute")

        result = SourceQueryExecutorFactory.get_source_query_executor("bad_source")

        self.assertIsNone(result)

    @patch("insights.sources.factories.import_string")
    def test_returns_none_on_unexpected_error(self, mock_import_string):
        mock_import_string.side_effect = RuntimeError("Something went wrong")

        result = SourceQueryExecutorFactory.get_source_query_executor("broken_source")

        self.assertIsNone(result)

    @patch("insights.sources.factories.import_string")
    def test_constructs_correct_import_path(self, mock_import_string):
        mock_import_string.return_value = object()

        SourceQueryExecutorFactory.get_source_query_executor("vtex_conversions")

        mock_import_string.assert_called_once_with(
            "insights.sources.vtex_conversions.usecases.query_execute.QueryExecutor"
        )
