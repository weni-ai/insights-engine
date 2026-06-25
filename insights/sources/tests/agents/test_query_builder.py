from django.test import SimpleTestCase

from insights.sources.agents.query_builder import AgentSQLQueryBuilder
from insights.sources.filter_strategies import PostgreSQLFilterStrategy


class AgentSQLQueryBuilderTest(SimpleTestCase):
    def test_list_excludes_removed_by_default(self):
        builder = AgentSQLQueryBuilder()
        strategy = PostgreSQLFilterStrategy()
        builder.add_filter(strategy, "project_id", "eq", "proj-1", "pp")
        builder.build_query()

        query, params = builder.list()

        self.assertIn("pp.is_deleted = %s", query)
        self.assertEqual(params, ["proj-1", False])

    def test_list_include_removed_skips_is_deleted_filter(self):
        builder = AgentSQLQueryBuilder()
        strategy = PostgreSQLFilterStrategy()
        builder.add_filter(strategy, "project_id", "eq", "proj-1", "pp")
        builder.build_query()

        query, params = builder.list(include_removed=True)

        self.assertNotIn("is_deleted", query)
        self.assertEqual(params, ["proj-1"])
