from django.test import TestCase
from unittest.mock import Mock

from insights.sources.clients import (
    GenericSQLQueryGenerator,
    GenericElasticSearchQueryGenerator,
)


class TestGenericSQLQueryGenerator(TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_filter_strategy = Mock()
        self.mock_query_builder = Mock()
        self.mock_filterset = Mock()
        self.filters = {"field1": "value1", "field2__gte": "2023-01-01"}
        self.query_type = "count"
        self.query_kwargs = {"limit": 10}

        # Create instance
        self.generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=self.filters,
            query_type=self.query_type,
            query_kwargs=self.query_kwargs,
        )

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters provided."""
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"test": "value"},
            query_type="list",
            query_kwargs={"param": "value"},
        )

        self.assertEqual(generator.filter_strategy, self.mock_filter_strategy)
        self.assertEqual(generator.query_builder, self.mock_query_builder)
        self.assertEqual(generator.filterset, self.mock_filterset)
        self.assertEqual(generator.filters, {"test": "value"})
        self.assertEqual(generator.query_type, "list")
        self.assertEqual(generator.query_kwargs, {"param": "value"})

    def test_initialization_with_default_query_type(self):
        """Test initialization with default query_type when not provided."""
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
        )

        self.assertEqual(generator.query_type, "count")
        self.assertEqual(generator.query_kwargs, {})

    def test_initialization_with_empty_query_type_uses_default(self):
        """Test initialization with empty query_type uses default."""
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
            query_type="",
        )

        self.assertEqual(generator.query_type, "count")

    def test_generate_with_simple_field_filter(self):
        """Test generate method with simple field filter (no operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with simple field
        filters = {"field1": "value1"}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        result = generator.generate()

        # Verify calls
        self.mock_filter_strategy.assert_called_once()
        self.mock_query_builder.assert_called_once()
        self.mock_filterset.assert_called_once()
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "eq", "value1", "table_alias"
        )
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})
        self.assertEqual(result, ("SELECT COUNT(*) FROM table", []))

    def test_generate_with_field_operation_filter(self):
        """Test generate method with field operation filter (field__operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with field operation
        filters = {"field1__gte": "2023-01-01"}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "gte", "2023-01-01", "table_alias"
        )

    def test_generate_with_list_value_filter(self):
        """Test generate method with list value filter (automatically uses 'in' operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with list value
        filters = {"field1": ["value1", "value2", "value3"]}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance,
            "source_field",
            "in",
            ["value1", "value2", "value3"],
            "table_alias",
        )

    def test_generate_with_list_value_and_operation(self):
        """Test generate method with list value and field operation."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with list value and operation
        filters = {"field1__in": ["value1", "value2", "value3"]}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance,
            "source_field",
            "in",
            ["value1", "value2", "value3"],
            "table_alias",
        )

    def test_generate_with_join_clause(self):
        """Test generate method with field that has join clause."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {"join1": "INNER JOIN table1 ON condition"}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with join clause
        filters = {"field1": "value1"}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_builder_instance.add_joins.assert_called_once_with(
            {"join1": "INNER JOIN table1 ON condition"}
        )
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "eq", "value1", "table_alias"
        )

    def test_generate_with_empty_join_clause(self):
        """Test generate method with field that has empty join clause."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with empty join clause
        filters = {"field1": "value1"}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify add_joins is not called
        mock_builder_instance.add_joins.assert_not_called()

    def test_generate_with_nonexistent_field(self):
        """Test generate method with field that doesn't exist in filterset."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = None  # Field doesn't exist
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with nonexistent field
        filters = {"nonexistent_field": "value1"}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify field lookup was attempted but filter was not added
        mock_filterset_instance.get_field.assert_called_once_with("nonexistent_field")
        mock_builder_instance.add_filter.assert_not_called()
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})

    def test_generate_with_multiple_filters(self):
        """Test generate method with multiple filters."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        # Mock field objects
        field1_object = Mock()
        field1_object.source_field = "source_field1"
        field1_object.table_alias = "table_alias1"
        field1_object.join_clause = {}

        field2_object = Mock()
        field2_object.source_field = "source_field2"
        field2_object.table_alias = "table_alias2"
        field2_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance

        # Mock get_field to return different objects based on field name
        def mock_get_field(field_name):
            if field_name == "field1":
                return field1_object
            elif field_name == "field2":
                return field2_object
            return None

        mock_filterset_instance.get_field.side_effect = mock_get_field
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with multiple filters
        filters = {
            "field1": "value1",
            "field2__gte": "2023-01-01",
            "nonexistent_field": "value3",  # This should be skipped
        }
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        self.assertEqual(mock_filterset_instance.get_field.call_count, 3)
        self.assertEqual(
            mock_builder_instance.add_filter.call_count, 2
        )  # Only 2 valid fields
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})

    def test_generate_with_query_kwargs(self):
        """Test generate method with query kwargs passed to the query method."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with query kwargs
        query_kwargs = {"limit": 10, "offset": 20}
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"field1": "value1"},
            query_type="count",
            query_kwargs=query_kwargs,
        )

        generator.generate()

        # Verify query method called with kwargs
        mock_builder_instance.count.assert_called_once_with(**query_kwargs)

    def test_generate_with_different_query_type(self):
        """Test generate method with different query type."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"
        mock_field_object.table_alias = "table_alias"
        mock_field_object.join_clause = {}

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.list.return_value = ("SELECT * FROM table", [])

        # Test with list query type
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"field1": "value1"},
            query_type="list",
        )

        generator.generate()

        # Verify list method was called instead of count
        mock_builder_instance.list.assert_called_once_with(**{})
        mock_builder_instance.count.assert_not_called()

    def test_generate_with_empty_filters(self):
        """Test generate method with empty filters dictionary."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_builder_instance.count.return_value = ("SELECT COUNT(*) FROM table", [])

        # Test with empty filters
        generator = GenericSQLQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
            query_type="count",
        )

        generator.generate()

        # Verify no filters were processed
        mock_filterset_instance.get_field.assert_not_called()
        mock_builder_instance.add_filter.assert_not_called()
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})


class TestGenericElasticSearchQueryGenerator(TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_filter_strategy = Mock()
        self.mock_query_builder = Mock()
        self.mock_filterset = Mock()
        self.filters = {"field1": "value1", "field2__gte": "2023-01-01"}
        self.query_type = "count"
        self.query_kwargs = {"limit": 10}

        # Create instance
        self.generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=self.filters,
            query_type=self.query_type,
            query_kwargs=self.query_kwargs,
        )

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters provided."""
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"test": "value"},
            query_type="list",
            query_kwargs={"param": "value"},
        )

        self.assertEqual(generator.filter_strategy, self.mock_filter_strategy)
        self.assertEqual(generator.query_builder, self.mock_query_builder)
        self.assertEqual(generator.filterset, self.mock_filterset)
        self.assertEqual(generator.filters, {"test": "value"})
        self.assertEqual(generator.query_type, "list")
        self.assertEqual(generator.query_kwargs, {"param": "value"})

    def test_initialization_with_default_query_type(self):
        """Test initialization with default query_type when not provided."""
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
        )

        self.assertEqual(generator.query_type, "count")
        self.assertEqual(generator.query_kwargs, {})

    def test_initialization_with_empty_query_type_uses_default(self):
        """Test initialization with empty query_type uses default."""
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
            query_type="",
        )

        self.assertEqual(generator.query_type, "count")

    def test_generate_with_simple_field_filter(self):
        """Test generate method with simple field filter (no operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with simple field
        filters = {"field1": "value1"}
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        result = generator.generate()

        # Verify calls
        self.mock_filter_strategy.assert_called_once()
        self.mock_query_builder.assert_called_once()
        self.mock_filterset.assert_called_once()
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "eq", "value1"
        )
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})
        self.assertEqual(result, ("endpoint", {"query": "body"}))

    def test_generate_with_field_operation_filter(self):
        """Test generate method with field operation filter (field__operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with field operation
        filters = {"field1__gte": "2023-01-01"}
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "gte", "2023-01-01"
        )

    def test_generate_with_list_value_filter(self):
        """Test generate method with list value filter (automatically uses 'in' operation)."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with list value
        filters = {"field1": ["value1", "value2", "value3"]}
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        mock_filterset_instance.get_field.assert_called_once_with("field1")
        mock_builder_instance.add_filter.assert_called_once_with(
            mock_strategy_instance, "source_field", "in", ["value1", "value2", "value3"]
        )

    def test_generate_with_nonexistent_field(self):
        """Test generate method with field that doesn't exist in filterset."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = None  # Field doesn't exist
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with nonexistent field
        filters = {"nonexistent_field": "value1"}
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify field lookup was attempted but filter was not added
        mock_filterset_instance.get_field.assert_called_once_with("nonexistent_field")
        mock_builder_instance.add_filter.assert_not_called()
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})

    def test_generate_with_multiple_filters(self):
        """Test generate method with multiple filters."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        # Mock field objects
        field1_object = Mock()
        field1_object.source_field = "source_field1"

        field2_object = Mock()
        field2_object.source_field = "source_field2"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance

        # Mock get_field to return different objects based on field name
        def mock_get_field(field_name):
            if field_name == "field1":
                return field1_object
            elif field_name == "field2":
                return field2_object
            return None

        mock_filterset_instance.get_field.side_effect = mock_get_field
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with multiple filters
        filters = {
            "field1": "value1",
            "field2__gte": "2023-01-01",
            "nonexistent_field": "value3",  # This should be skipped
        }
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters=filters,
            query_type="count",
        )

        generator.generate()

        # Verify calls
        self.assertEqual(mock_filterset_instance.get_field.call_count, 3)
        self.assertEqual(
            mock_builder_instance.add_filter.call_count, 2
        )  # Only 2 valid fields
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})

    def test_generate_with_query_kwargs(self):
        """Test generate method with query kwargs passed to the query method."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with query kwargs
        query_kwargs = {"limit": 10, "offset": 20}
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"field1": "value1"},
            query_type="count",
            query_kwargs=query_kwargs,
        )

        generator.generate()

        # Verify query method called with kwargs
        mock_builder_instance.count.assert_called_once_with(**query_kwargs)

    def test_generate_with_different_query_type(self):
        """Test generate method with different query type."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()
        mock_field_object = Mock()
        mock_field_object.source_field = "source_field"

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_filterset_instance.get_field.return_value = mock_field_object
        mock_builder_instance.list.return_value = ("endpoint", {"query": "body"})

        # Test with list query type
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={"field1": "value1"},
            query_type="list",
        )

        generator.generate()

        # Verify list method was called instead of count
        mock_builder_instance.list.assert_called_once_with(**{})
        mock_builder_instance.count.assert_not_called()

    def test_generate_with_empty_filters(self):
        """Test generate method with empty filters dictionary."""
        # Setup mocks
        mock_strategy_instance = Mock()
        mock_builder_instance = Mock()
        mock_filterset_instance = Mock()

        self.mock_filter_strategy.return_value = mock_strategy_instance
        self.mock_query_builder.return_value = mock_builder_instance
        self.mock_filterset.return_value = mock_filterset_instance
        mock_builder_instance.count.return_value = ("endpoint", {"query": "body"})

        # Test with empty filters
        generator = GenericElasticSearchQueryGenerator(
            filter_strategy=self.mock_filter_strategy,
            query_builder=self.mock_query_builder,
            filterset=self.mock_filterset,
            filters={},
            query_type="count",
        )

        generator.generate()

        # Verify no filters were processed
        mock_filterset_instance.get_field.assert_not_called()
        mock_builder_instance.add_filter.assert_not_called()
        mock_builder_instance.build_query.assert_called_once()
        mock_builder_instance.count.assert_called_once_with(**{})
