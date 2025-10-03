from django.test import TestCase
from unittest.mock import Mock

from insights.sources.flowruns.query_builder import FlowRunElasticSearchQueryBuilder
from insights.sources.filter_strategies import ElasticSearchFilterStrategy


class FlowRunElasticSearchQueryBuilderTestCase(TestCase):

    def setUp(self):
        self.query_builder = FlowRunElasticSearchQueryBuilder()
        self.strategy = ElasticSearchFilterStrategy()

    def test_init(self):
        """Test query builder initialization"""
        self.assertEqual(self.query_builder.query_clauses, {})
        self.assertFalse(self.query_builder.is_valid)

    def test_add_filter_eq_operation(self):
        """Test adding a filter with eq operation"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")

        expected_clauses = {"must": {"term": {"project": "test-project"}}}
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_filter_gte_operation(self):
        """Test adding a filter with gte operation"""
        self.query_builder.add_filter(self.strategy, "created_on", "gte", "2023-01-01")

        expected_clauses = {"must": {"range": {"created_on": {"gte": "2023-01-01"}}}}
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_filter_lte_operation(self):
        """Test adding a filter with lte operation"""
        self.query_builder.add_filter(self.strategy, "created_on", "lte", "2023-12-31")

        expected_clauses = {"must": {"range": {"created_on": {"lte": "2023-12-31"}}}}
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_filter_after_operation(self):
        """Test adding a filter with after operation (should map to gte)"""
        self.query_builder.add_filter(
            self.strategy, "created_on", "after", "2023-01-01"
        )

        expected_clauses = {"must": {"range": {"created_on": {"gte": "2023-01-01"}}}}
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_filter_before_operation(self):
        """Test adding a filter with before operation (should map to lte)"""
        self.query_builder.add_filter(
            self.strategy, "created_on", "before", "2023-12-31"
        )

        expected_clauses = {"must": {"range": {"created_on": {"lte": "2023-12-31"}}}}
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_multiple_filters_same_operation(self):
        """Test adding multiple filters with the same operation"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "project-1")
        self.query_builder.add_filter(self.strategy, "flow", "eq", "flow-1")

        expected_clauses = {
            "must": {"term": {"project": "project-1", "flow": "flow-1"}}
        }
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_multiple_filters_different_operations(self):
        """Test adding multiple filters with different operations"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "project-1")
        self.query_builder.add_filter(self.strategy, "created_on", "gte", "2023-01-01")

        expected_clauses = {
            "must": {
                "term": {"project": "project-1"},
                "range": {"created_on": {"gte": "2023-01-01"}},
            }
        }
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_add_filter_range_update(self):
        """Test adding range filters that should update existing range"""
        self.query_builder.add_filter(self.strategy, "created_on", "gte", "2023-01-01")
        self.query_builder.add_filter(self.strategy, "created_on", "lte", "2023-12-31")

        expected_clauses = {
            "must": {
                "range": {"created_on": {"gte": "2023-01-01", "lte": "2023-12-31"}}
            }
        }
        self.assertEqual(self.query_builder.query_clauses, expected_clauses)

    def test_build_query_empty_clauses(self):
        """Test building query with empty clauses"""
        self.query_builder.build_query()

        expected_query = {"bool": {}}
        self.assertEqual(self.query_builder.validated_query, expected_query)
        self.assertTrue(self.query_builder.is_valid)

    def test_build_query_with_clauses(self):
        """Test building query with existing clauses"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.add_filter(self.strategy, "created_on", "gte", "2023-01-01")

        self.query_builder.build_query()

        expected_query = {
            "bool": {
                "must": [
                    {"term": {"project": "test-project"}},
                    {"range": {"created_on": {"gte": "2023-01-01"}}},
                ]
            }
        }
        self.assertEqual(self.query_builder.validated_query, expected_query)
        self.assertTrue(self.query_builder.is_valid)

    def test_count(self):
        """Test count method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.count()

        self.assertEqual(endpoint, "_count")
        self.assertEqual(params, {"query": self.query_builder.validated_query})

    def test_sum(self):
        """Test sum aggregation method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.sum("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertIn("values", params["aggs"])
        self.assertIn("nested", params["aggs"]["values"])
        self.assertEqual(params["aggs"]["values"]["nested"]["path"], "values")
        self.assertIn("agg_field", params["aggs"]["values"]["aggs"])
        self.assertIn(
            "agg_value", params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]
        )
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["sum"][
                "field"
            ],
            "values.value_number",
        )

    def test_avg(self):
        """Test avg aggregation method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.avg("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["avg"][
                "field"
            ],
            "values.value_number",
        )

    def test_max(self):
        """Test max aggregation method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.max("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["max"][
                "field"
            ],
            "values.value_number",
        )

    def test_min(self):
        """Test min aggregation method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.min("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["min"][
                "field"
            ],
            "values.value_number",
        )

    def test_recurrence_default_limit(self):
        """Test recurrence method with default limit"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.recurrence("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "size"
            ],
            100,
        )
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "field"
            ],
            "values.value",
        )
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "execution_hint"
            ],
            "map",
        )

    def test_recurrence_custom_limit(self):
        """Test recurrence method with custom limit"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.recurrence("test_field", limit=50)

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "size"
            ],
            50,
        )

    def test_count_value(self):
        """Test count_value method"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.count_value("test_field", "test_value")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)

        # Check the filter structure
        filter_conditions = params["aggs"]["values"]["aggs"]["agg_field"]["filter"][
            "bool"
        ]["filter"]
        self.assertEqual(len(filter_conditions), 2)
        self.assertIn({"term": {"values.name": "test_field"}}, filter_conditions)
        self.assertIn({"term": {"values.value": "test_value"}}, filter_conditions)

        # Check aggregation structure
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "size"
            ],
            1,
        )
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "field"
            ],
            "values.value",
        )

    def test_list_values_default_limit(self):
        """Test list_values method with default limit"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.list_values("test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "size"
            ],
            100,
        )

    def test_list_values_custom_limit(self):
        """Test list_values method with custom limit"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder.list_values("test_field", limit=200)

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["terms"][
                "size"
            ],
            200,
        )

    def test_base_operation_custom_value_field(self):
        """Test _base_operation with custom value_field"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder._base_operation(
            "sum", "test_field", "custom.value_field"
        )

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["sum"][
                "field"
            ],
            "custom.value_field",
        )

    def test_base_operation_default_value_field(self):
        """Test _base_operation with default value_field"""
        self.query_builder.add_filter(self.strategy, "project", "eq", "test-project")
        self.query_builder.build_query()

        endpoint, params = self.query_builder._base_operation("sum", "test_field")

        self.assertEqual(endpoint, "_search")
        self.assertEqual(params["size"], 0)
        self.assertEqual(params["query"], self.query_builder.validated_query)
        self.assertIn("aggs", params)
        self.assertEqual(
            params["aggs"]["values"]["aggs"]["agg_field"]["aggs"]["agg_value"]["sum"][
                "field"
            ],
            "values.value_number",
        )

    def test_aggregation_methods_without_build_query(self):
        """Test that aggregation methods work even without calling build_query first"""
        # This should raise an AttributeError since validated_query doesn't exist
        with self.assertRaises(AttributeError):
            self.query_builder.sum("test_field")

    def test_count_without_build_query(self):
        """Test that count method works even without calling build_query first"""
        # This should raise an AttributeError since validated_query doesn't exist
        with self.assertRaises(AttributeError):
            self.query_builder.count()

    def test_complex_query_structure(self):
        """Test building a complex query with multiple filters and operations"""
        # Add multiple filters
        self.query_builder.add_filter(self.strategy, "project", "eq", "project-1")
        self.query_builder.add_filter(self.strategy, "flow", "eq", "flow-1")
        self.query_builder.add_filter(self.strategy, "created_on", "gte", "2023-01-01")
        self.query_builder.add_filter(self.strategy, "created_on", "lte", "2023-12-31")
        self.query_builder.add_filter(self.strategy, "exited_on", "gte", "2023-06-01")

        self.query_builder.build_query()

        # Test that the query structure is correct
        expected_query = {
            "bool": {
                "must": [
                    {"term": {"project": "project-1"}},
                    {"term": {"flow": "flow-1"}},
                    {
                        "range": {
                            "created_on": {"gte": "2023-01-01", "lte": "2023-12-31"}
                        }
                    },
                    {"range": {"exited_on": {"gte": "2023-06-01"}}},
                ]
            }
        }
        self.assertEqual(self.query_builder.validated_query, expected_query)
        self.assertTrue(self.query_builder.is_valid)

    def test_strategy_apply_method_called(self):
        """Test that the strategy's apply method is called with correct parameters"""
        mock_strategy = Mock()
        mock_strategy.apply.return_value = ("test_field", "test_value", "must", "term")

        self.query_builder.add_filter(mock_strategy, "field", "operation", "value")

        mock_strategy.apply.assert_called_once_with("field", "operation", "value")

    def test_strategy_apply_with_args_kwargs(self):
        """Test that strategy apply method receives only the first 3 arguments"""
        mock_strategy = Mock()
        mock_strategy.apply.return_value = ("test_field", "test_value", "must", "term")

        self.query_builder.add_filter(
            mock_strategy,
            "field",
            "operation",
            "value",
            "arg1",
            "arg2",
            kwarg1="value1",
            kwarg2="value2",
        )

        # The strategy apply method is only called with the first 3 arguments
        # The *args and **kwargs are accepted by add_filter but not passed to strategy.apply
        mock_strategy.apply.assert_called_once_with("field", "operation", "value")
