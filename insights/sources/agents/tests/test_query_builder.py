from django.test import TestCase

from insights.sources.agents.query_builder import (
    AgentSQLQueryBuilder,
    ProjectAdminsAndManagersSQLQueryBuilder,
)


class TestAgentSQLQueryBuilder(TestCase):
    def setUp(self):
        self.builder = AgentSQLQueryBuilder()

    def test_list_query_does_not_filter_by_role(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, params = self.builder.list()

        self.assertIn(
            "FROM public.projects_projectpermission AS pp", query
        )
        self.assertNotIn("sectors_sectorauthorization", query)
        self.assertIn("pp.is_deleted = %s", query)
        self.assertEqual(params, ["project-uuid", False])

    def test_list_query_excludes_soft_deleted(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, params = self.builder.list()

        self.assertIn("pp.is_deleted = %s", query)
        self.assertEqual(params, ["project-uuid", False])


class TestProjectAdminsAndManagersSQLQueryBuilder(TestCase):
    def setUp(self):
        self.builder = ProjectAdminsAndManagersSQLQueryBuilder()

    def test_list_query_includes_sector_authorization_join(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, params = self.builder.list()

        self.assertIn(
            "LEFT JOIN public.sectors_sectorauthorization AS sa", query
        )
        self.assertIn("sa.permission_id=pp.uuid AND sa.role=1", query)
        self.assertEqual(params, ["project-uuid", False])

    def test_list_query_filters_by_admin_or_manager_role(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, _ = self.builder.list()

        self.assertIn(
            "WHERE pp.project_id = (%s) AND (pp.role=1 OR sa.role=1)", query
        )

    def test_list_query_excludes_soft_deleted(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, params = self.builder.list()

        self.assertIn("pp.is_deleted = %s", query)
        self.assertEqual(params, ["project-uuid", False])

    def test_list_query_uses_distinct_to_avoid_duplicated_rows(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]

        query, _ = self.builder.list()

        self.assertTrue(query.startswith("SELECT DISTINCT"))

    def test_build_query_is_called_when_not_valid(self):
        self.builder.where_clauses = ["pp.project_id = (%s)"]
        self.builder.params = ["project-uuid"]
        self.builder.is_valid = False

        query, _ = self.builder.list()

        self.assertTrue(self.builder.is_valid)
        self.assertIn("pp.project_id = (%s)", query)
