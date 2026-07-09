from unittest.mock import MagicMock, patch

from django.test import TestCase

from insights.sources.agents.usecases.query_execute import (
    ProjectAdminsAndManagersQueryExecutor,
    QueryExecutor,
)


class TestProjectAdminsAndManagersQueryExecutor(TestCase):
    @patch("insights.sources.agents.usecases.query_execute.get_cursor")
    @patch("insights.sources.agents.usecases.query_execute.dictfetchall")
    @patch("insights.sources.agents.usecases.query_execute.AgentSQLQueryGenerator")
    def test_execute_uses_project_admins_and_managers_query_builder(
        self, mock_query_generator_cls, mock_dictfetchall, mock_get_cursor
    ):
        mock_query_generator = MagicMock()
        mock_query_generator.generate.return_value = ("SELECT 1", [])
        mock_query_generator_cls.return_value = mock_query_generator

        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_dictfetchall.return_value = [{"uuid": "1", "email": "a@a.com"}]

        result = ProjectAdminsAndManagersQueryExecutor.execute(
            filters={"project": "project-uuid"},
            operation="list",
            parser=lambda x: x,
            return_format="select_input",
        )

        self.assertEqual(
            mock_query_generator_cls.call_args.kwargs["query_builder"],
            ProjectAdminsAndManagersQueryExecutor.query_builder,
        )
        self.assertEqual(result["results"], [{"uuid": "1", "email": "a@a.com"}])

    def test_query_builder_differs_from_base_executor(self):
        self.assertNotEqual(
            QueryExecutor.query_builder,
            ProjectAdminsAndManagersQueryExecutor.query_builder,
        )
