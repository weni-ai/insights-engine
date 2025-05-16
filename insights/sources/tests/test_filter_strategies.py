from django.test import TestCase
from insights.sources.filter_strategies import (
    PostgreSQLFilterStrategy,
    ElasticSearchFilterStrategy,
)


class PostgreSQLFilterStrategyTests(TestCase):
    def setUp(self):
        self.strategy = PostgreSQLFilterStrategy()
        self.table_alias = "test_table"

    def test_after_operation(self):
        field = "created_at"
        value = "2024-01-01"
        query, params = self.strategy.apply(field, "after", value, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} >= (%s)")
        self.assertEqual(params, [value])

    def test_before_operation(self):
        field = "created_at"
        value = "2024-01-01"
        query, params = self.strategy.apply(field, "before", value, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} <= (%s)")
        self.assertEqual(params, [value])

    def test_eq_operation(self):
        field = "status"
        value = "active"
        query, params = self.strategy.apply(field, "eq", value, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} = (%s)")
        self.assertEqual(params, [value])

    def test_in_operation(self):
        field = "id"
        value = [1, 2, 3]
        query, params = self.strategy.apply(field, "in", value, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} IN (%s, %s, %s)")
        self.assertEqual(params, value)

    def test_icontains_operation(self):
        field = "name"
        value = "test"
        query, params = self.strategy.apply(field, "icontains", value, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} ILIKE (%s)")
        self.assertEqual(params, [f"%{value}%"])

    def test_isnull_operation_true(self):
        field = "deleted_at"
        query, params = self.strategy.apply(field, "isnull", True, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} IS NULL")
        self.assertIsNone(params)

    def test_isnull_operation_false(self):
        field = "deleted_at"
        query, params = self.strategy.apply(field, "isnull", False, self.table_alias)
        self.assertEqual(query, f"{self.table_alias}.{field} IS NOT NULL")
        self.assertIsNone(params)

    def test_or_operation(self):
        field = {"name": "users", "email": "users"}
        value = "john"
        query, params = self.strategy.apply(field, "or", value, self.table_alias)
        expected_query = "(users.name ILIKE (%s) OR users.email ILIKE (%s))"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, [f"%{value}%", f"%{value}%"])

    def test_or_operation_invalid_field(self):
        field = "invalid_field"
        value = "test"
        with self.assertRaises(ValueError) as context:
            self.strategy.apply(field, "or", value, self.table_alias)
        self.assertEqual(
            str(context.exception),
            "On 'or' operations, the field needs to be a dict sub_field_name: sub_table_alias",
        )

    def test_unsupported_operation(self):
        field = "name"
        value = "test"
        with self.assertRaises(ValueError) as context:
            self.strategy.apply(field, "unsupported", value, self.table_alias)
        self.assertEqual(str(context.exception), "Unsupported operation: unsupported")


class ElasticSearchFilterStrategyTests(TestCase):
    def setUp(self):
        self.strategy = ElasticSearchFilterStrategy()

    def test_eq_operation(self):
        field = "status"
        value = "active"
        field_name, query_value, query_block, query_operation = self.strategy.apply(
            field, "eq", value
        )
        self.assertEqual(field_name, field)
        self.assertEqual(query_value, value)
        self.assertEqual(query_block, "must")
        self.assertEqual(query_operation, "term")

    def test_after_operation(self):
        field = "created_at"
        value = "2024-01-01"
        field_name, query_value, query_block, query_operation = self.strategy.apply(
            field, "after", value
        )
        self.assertEqual(field_name, field)
        self.assertEqual(query_value, {"gte": value})
        self.assertEqual(query_block, "must")
        self.assertEqual(query_operation, "range")

    def test_before_operation(self):
        field = "created_at"
        value = "2024-01-01"
        field_name, query_value, query_block, query_operation = self.strategy.apply(
            field, "before", value
        )
        self.assertEqual(field_name, field)
        self.assertEqual(query_value, {"lte": value})
        self.assertEqual(query_block, "must")
        self.assertEqual(query_operation, "range")

    def test_gte_operation(self):
        field = "age"
        value = 18
        field_name, query_value, query_block, query_operation = self.strategy.apply(
            field, "gte", value
        )
        self.assertEqual(field_name, field)
        self.assertEqual(query_value, {"gte": value})
        self.assertEqual(query_block, "must")
        self.assertEqual(query_operation, "range")

    def test_lte_operation(self):
        field = "price"
        value = 100
        field_name, query_value, query_block, query_operation = self.strategy.apply(
            field, "lte", value
        )
        self.assertEqual(field_name, field)
        self.assertEqual(query_value, {"lte": value})
        self.assertEqual(query_block, "must")
        self.assertEqual(query_operation, "range")
