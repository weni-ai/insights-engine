from datetime import datetime
from django.test import TestCase
from unittest.mock import MagicMock, patch, PropertyMock
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from insights.widgets.models import Widget
from insights.widgets.usecases.get_source_data import (
    set_live_day,
    apply_timezone_to_filters,
    format_date,
    convert_to_iso,
    simple_source_data_operation,
    cross_source_data_operation,
    get_source_data_from_widget,
    Calculator,
)
from insights.projects.parsers import parse_dict_to_json
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class TestDateFunctions(TestCase):
    def setUp(self):
        self.default_filters = {
            "created_at__gte": "today",
            "created_at__lte": "2024-03-20",
            "updated_at__gte": "2024-03-19",
            "updated_at__lte": "today",
        }

    def test_set_live_day(self):
        """Test that 'today' values are replaced with start of current day"""
        set_live_day(self.default_filters)

        # Check that 'today' values were replaced with datetime objects
        self.assertIsInstance(self.default_filters["created_at__gte"], datetime)
        self.assertIsInstance(self.default_filters["updated_at__lte"], datetime)

        # Check that the time is set to start of day (00:00:00)
        self.assertEqual(self.default_filters["created_at__gte"].hour, 0)
        self.assertEqual(self.default_filters["created_at__gte"].minute, 0)
        self.assertEqual(self.default_filters["created_at__gte"].second, 0)

        # Check that non-'today' values remain unchanged
        self.assertEqual(self.default_filters["created_at__lte"], "2024-03-20")
        self.assertEqual(self.default_filters["updated_at__gte"], "2024-03-19")

    def test_apply_timezone_to_filters(self):
        """Test that datetime values are properly localized to project timezone"""
        # First set some datetime values
        test_filters = {
            "created_at__gte": datetime(2024, 3, 20),
            "created_at__lte": ["2024-03-20"],
            "updated_at__gte": datetime(2024, 3, 19),
            "updated_at__lte": datetime(2024, 3, 20),
        }

        project_timezone_str = "America/Sao_Paulo"
        apply_timezone_to_filters(test_filters, project_timezone_str)

        # Check that datetime values are timezone-aware
        self.assertIsNotNone(test_filters["created_at__gte"].tzinfo)
        self.assertEqual(
            test_filters["created_at__gte"].tzinfo.zone, project_timezone_str
        )

        # Check that list values are properly converted
        self.assertIsInstance(test_filters["created_at__lte"], datetime)

        converted_value = test_filters["created_at__lte"]
        if isinstance(converted_value, datetime):
            self.assertIsNotNone(converted_value.tzinfo)
            self.assertEqual(converted_value.tzinfo.zone, project_timezone_str)
        else:
            self.fail("test_filters['created_at__lte'] was not converted to datetime")

        # Check that all datetime values have timezone
        for key, value in test_filters.items():
            if isinstance(value, datetime):
                self.assertIsNotNone(value.tzinfo)
                self.assertEqual(value.tzinfo.zone, project_timezone_str)

    def test_format_date(self):
        """Test that datetime values are properly formatted with start/end of day"""
        # Set up test data
        test_date = datetime(2024, 3, 20, 15, 30, 45)
        self.default_filters = {
            "created_at__gte": test_date,
            "created_at__lte": test_date,
        }

        format_date(self.default_filters)

        # Check that __gte dates are set to start of day
        self.assertEqual(self.default_filters["created_at__gte"].hour, 0)
        self.assertEqual(self.default_filters["created_at__gte"].minute, 0)
        self.assertEqual(self.default_filters["created_at__gte"].second, 0)
        self.assertEqual(self.default_filters["created_at__gte"].microsecond, 0)

        # Check that __lte dates are set to end of day
        self.assertEqual(self.default_filters["created_at__lte"].hour, 23)
        self.assertEqual(self.default_filters["created_at__lte"].minute, 59)
        self.assertEqual(self.default_filters["created_at__lte"].second, 59)
        self.assertEqual(self.default_filters["created_at__lte"].microsecond, 999999)

    def test_convert_to_iso(self):
        """Test that datetime values are converted to ISO format strings"""
        # Set up test data
        test_date = datetime(2024, 3, 20, 15, 30, 45)
        self.default_filters = {
            "created_at": test_date,
            "updated_at": "2024-03-20",  # Non-datetime value
        }

        convert_to_iso(self.default_filters)

        # Check that datetime was converted to ISO format string
        self.assertIsInstance(self.default_filters["created_at"], str)
        self.assertEqual(self.default_filters["created_at"], "2024-03-20T15:30:45")

        # Check that non-datetime values remain unchanged
        self.assertEqual(self.default_filters["updated_at"], "2024-03-20")


class TestCalculator(TestCase):
    def test_calculator_operations(self):
        # Test sum
        calc_sum = Calculator(10, 5, "sum")
        self.assertEqual(calc_sum.evaluate(), 15)

        # Test sub
        calc_sub = Calculator(10, 5, "sub")
        self.assertEqual(calc_sub.evaluate(), 5)

        # Test multiply
        calc_multiply = Calculator(10, 5, "multiply")
        self.assertEqual(calc_multiply.evaluate(), 50)

        # Test percentage
        calc_percentage = Calculator(50, 100, "percentage")
        self.assertEqual(calc_percentage.evaluate(), 50.0)

        with self.assertRaises(AttributeError):  # Test invalid operator
            Calculator(1, 1, "invalid").evaluate()


class TestDataSourceOperations(TestCase):
    def setUp(self):
        self.widget_mock = MagicMock(spec=Widget)
        self.widget_mock.project.timezone = "America/Sao_Paulo"
        self.widget_mock.project.uuid = "test_project_uuid"
        self.widget_mock.source_config.return_value = ({}, "list", None, None, None)
        self.widget_mock.is_crossing_data = False
        self.widget_mock.type = "some_type"

        self.source_query_mock = MagicMock()
        self.source_query_mock.execute.return_value = {"value": "test_data"}

    def test_simple_source_data_operation_basic(self):
        filters = {"slug": ["subwidget_1"]}
        result = simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
        )
        self.assertEqual(result, {"value": "test_data"})
        self.source_query_mock.execute.assert_called_once()
        self.widget_mock.source_config.assert_called_once_with(
            sub_widget="subwidget_1", is_live=False
        )

    @patch("insights.widgets.usecases.get_source_data.set_live_day")
    def test_simple_source_data_operation_live(self, mock_set_live_day):
        filters = {"slug": ["subwidget_1"]}
        current_filters_for_source_config = {"created_at__gte": "today"}
        self.widget_mock.source_config.return_value = (
            current_filters_for_source_config,
            "list",
            None,
            None,
            None,
        )

        def mock_set_live_day_side_effect(default_filters_arg):
            start_of_day = datetime.combine(datetime.now().date(), datetime.min.time())
            if default_filters_arg.get("created_at__gte") == "today":
                default_filters_arg["created_at__gte"] = start_of_day

        mock_set_live_day.side_effect = mock_set_live_day_side_effect

        self.source_query_mock.execute.reset_mock()

        result = simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
            is_live=True,
        )
        self.assertEqual(result, {"value": "test_data"})
        mock_set_live_day.assert_called_once()

        self.source_query_mock.execute.assert_called_once()

        final_filters_for_execute = self.source_query_mock.execute.call_args.kwargs[
            "filters"
        ]
        self.assertIsInstance(final_filters_for_execute["created_at__gte"], str)

        try:
            datetime.fromisoformat(
                final_filters_for_execute["created_at__gte"].replace("Z", "+00:00")
            )
        except ValueError:
            self.fail("created_at__gte is not a valid ISO date string")

    def test_simple_source_data_operation_with_op_fields_and_limit(self):
        filters = {"slug": ["subwidget_1"]}
        self.widget_mock.source_config.return_value = (
            {},
            "list",
            "test_op_field",
            "test_op_sub_field",
            10,
        )
        simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
        )
        self.source_query_mock.execute.assert_called_once()
        called_kwargs = self.source_query_mock.execute.call_args.kwargs
        self.assertEqual(called_kwargs["query_kwargs"]["op_field"], "test_op_field")
        self.assertEqual(
            called_kwargs["query_kwargs"]["op_sub_field"], "test_op_sub_field"
        )
        self.assertEqual(called_kwargs["query_kwargs"]["limit"], 10)

    def test_simple_source_data_operation_with_tags(self):
        filters = {"slug": ["subwidget_1"], "tags": ["tag1,tag2"]}
        self.widget_mock.source_config.return_value = ({}, "list", None, None, None)

        simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
        )

        self.source_query_mock.execute.assert_called_once()
        called_filters = self.source_query_mock.execute.call_args.kwargs["filters"]
        self.assertEqual(called_filters["tags"], ["tag1", "tag2"])

    def test_simple_source_data_operation_with_timeseries_kwargs(self):
        filters = {"slug": ["subwidget_1"]}
        extra_query_kwargs = {
            "timeseries_hour_kwargs": {"start_hour": 8, "end_hour": 17}
        }
        simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
            extra_query_kwargs=extra_query_kwargs,
        )
        self.source_query_mock.execute.assert_called_once()
        called_kwargs = self.source_query_mock.execute.call_args.kwargs["query_kwargs"]
        self.assertEqual(called_kwargs["start_hour"], 8)
        self.assertEqual(called_kwargs["end_hour"], 17)

    @patch("insights.widgets.usecases.get_source_data.simple_source_data_operation")
    def test_cross_source_data_operation(self, mock_simple_operation):
        mock_simple_operation.side_effect = [
            {"value": 100},
            {"value": 50},
        ]
        self.widget_mock.config = {"operator": "sum"}

        result = cross_source_data_operation(
            source_query=self.source_query_mock, widget=self.widget_mock
        )

        self.assertEqual(result, {"value": 150})
        self.assertEqual(mock_simple_operation.call_count, 2)

    @patch("insights.widgets.usecases.get_source_data.simple_source_data_operation")
    def test_cross_source_data_operation_percentage(self, mock_simple_operation):
        mock_simple_operation.side_effect = [
            {"value": 50},
            {"value": 100},
        ]
        self.widget_mock.config = {"operator": "percentage"}

        result = cross_source_data_operation(
            source_query=self.source_query_mock, widget=self.widget_mock
        )

        self.assertEqual(result, {"value": 50.0})

    def test_simple_source_data_operation_slug_as_list(self):
        filters = {"slug": ["subwidget_list_case"]}
        self.widget_mock.source_config.return_value = (
            {},
            "list",
            None,
            None,
            None,
        )

        simple_source_data_operation(
            source_query=self.source_query_mock,
            widget=self.widget_mock,
            filters=filters,
        )
        self.source_query_mock.execute.assert_called_once()
        self.widget_mock.source_config.assert_called_with(
            sub_widget="subwidget_list_case", is_live=False
        )


@patch("insights.widgets.usecases.get_source_data.simple_source_data_operation")
@patch("insights.widgets.usecases.get_source_data.get_source")
class TestGetSourceDataFromWidget(TestCase):
    def setUp(self):
        self.widget_mock = MagicMock(spec=Widget)
        self.widget_mock.source = "test_source"
        self.widget_mock.is_crossing_data = False
        self.widget_mock.type = "regular_type"
        self.widget_mock.name = "some_widget_name"

    def test_get_source_data_simple_operation(
        self, mock_get_source, mock_simple_operation
    ):
        mock_source_query = MagicMock()
        mock_get_source.return_value = mock_source_query
        mock_simple_operation.return_value = {"data": "simple_test_data"}

        result = get_source_data_from_widget(widget=self.widget_mock)

        self.assertEqual(result, {"data": "simple_test_data"})
        mock_get_source.assert_called_once_with(slug="test_source")
        mock_simple_operation.assert_called_once_with(
            widget=self.widget_mock,
            source_query=mock_source_query,
            is_live=False,
            filters={},
            user_email="",
            auth_params={},
            extra_query_kwargs={},
        )

    @patch("insights.widgets.usecases.get_source_data.cross_source_data_operation")
    def test_get_source_data_cross_operation(
        self, mock_cross_operation, mock_get_source, mock_simple_op_unused
    ):
        mock_source_query = MagicMock()
        mock_get_source.return_value = mock_source_query
        mock_cross_operation.return_value = {"data": "cross_test_data"}
        self.widget_mock.is_crossing_data = True

        result = get_source_data_from_widget(widget=self.widget_mock)

        self.assertEqual(result, {"data": "cross_test_data"})
        mock_get_source.assert_called_once_with(slug="test_source")
        mock_cross_operation.assert_called_once_with(
            widget=self.widget_mock,
            source_query=mock_source_query,
            is_live=False,
            filters={},
            user_email="",
            auth_params={},
            extra_query_kwargs={},
        )

    def test_get_source_data_vtex_order_auth(
        self, mock_get_source, mock_simple_operation
    ):
        mock_source_query = MagicMock()
        mock_vtex_auth_source = MagicMock()
        mock_get_source.side_effect = [mock_source_query, mock_vtex_auth_source]
        mock_vtex_auth_source.execute.return_value = {"auth": "vtex_token"}
        mock_simple_operation.return_value = {"data": "vtex_data"}

        self.widget_mock.type = "vtex_order"
        self.widget_mock.project.uuid = "vtex_project_uuid"

        result = get_source_data_from_widget(widget=self.widget_mock)

        self.assertEqual(result, {"data": "vtex_data"})
        mock_get_source.assert_any_call(slug="test_source")
        mock_get_source.assert_any_call(slug="vtexcredentials")
        mock_vtex_auth_source.execute.assert_called_once_with(
            filters={"project": "vtex_project_uuid"},
            operation="get_vtex_auth",
            parser=parse_dict_to_json,
            return_format="",
            query_kwargs={},
        )
        mock_simple_operation.assert_called_once()
        # Check that auth_params was passed to simple_operation
        self.assertEqual(
            mock_simple_operation.call_args.kwargs["auth_params"],
            {"auth": "vtex_token"},
        )

    def test_get_source_data_vtex_order_credentials_not_found(
        self, mock_get_source, mock_simple_operation
    ):
        """Test that PermissionDenied is raised when VTEX credentials are not found"""
        mock_source_query = MagicMock()
        mock_vtex_auth_source = MagicMock()
        mock_get_source.side_effect = [mock_source_query, mock_vtex_auth_source]

        # Simulate VtexCredentialsNotFound exception
        mock_vtex_auth_source.execute.side_effect = VtexCredentialsNotFound(
            "Credentials not found for project vtex_project_uuid"
        )

        self.widget_mock.type = "vtex_order"
        self.widget_mock.project.uuid = "vtex_project_uuid"

        # Verify that PermissionDenied is raised
        with self.assertRaises(PermissionDenied) as context:
            get_source_data_from_widget(widget=self.widget_mock)

        # Verify the error message
        self.assertIn("VTEX credentials not configured", str(context.exception.detail))

        # Verify that get_source was called for both sources
        mock_get_source.assert_any_call(slug="test_source")
        mock_get_source.assert_any_call(slug="vtexcredentials")

        # Verify that simple_operation was NOT called since auth failed
        mock_simple_operation.assert_not_called()

    def test_get_source_data_human_service_dashboard_report(
        self, mock_get_source, mock_simple_operation
    ):
        mock_source_query = MagicMock()
        mock_get_source.return_value = mock_source_query
        mock_simple_operation.return_value = {"data": "dashboard_data"}

        self.widget_mock.name = "human_service_dashboard.peaks_in_human_service"

        result = get_source_data_from_widget(widget=self.widget_mock, is_report=False)

        self.assertEqual(result, {"data": "dashboard_data"})
        expected_extra_kwargs = {
            "timeseries_hour_kwargs": {"start_hour": 7, "end_hour": 18}
        }
        mock_simple_operation.assert_called_once()
        self.assertEqual(
            mock_simple_operation.call_args.kwargs["extra_query_kwargs"],
            expected_extra_kwargs,
        )

    def test_get_source_data_source_not_found(
        self, mock_get_source, mock_simple_operation
    ):
        mock_get_source.return_value = None
        with self.assertRaisesMessage(
            Exception, "could not find a source with the slug test_source"
        ):
            get_source_data_from_widget(widget=self.widget_mock)

    def test_get_source_data_widget_not_found(
        self, mock_get_source, mock_simple_operation
    ):
        original_project_mock = self.widget_mock.project

        report_property_mock = PropertyMock(side_effect=ObjectDoesNotExist)
        type(self.widget_mock).report = report_property_mock
        self.widget_mock.project = original_project_mock

        mock_get_source.return_value = MagicMock()
        mock_simple_operation.return_value = MagicMock()

        with self.assertRaisesMessage(Exception, "Widget not found."):
            get_source_data_from_widget(widget=self.widget_mock, is_report=True)

        del type(self.widget_mock).report

    @patch("insights.widgets.usecases.get_source_data.cross_source_data_operation")
    def test_get_source_data_key_error_in_cross_operation(
        self, mock_cross_operation, mock_get_source, mock_simple_op_unused
    ):
        mock_source_query = MagicMock()
        mock_get_source.return_value = mock_source_query
        mock_cross_operation.side_effect = KeyError("Simulated KeyError")
        self.widget_mock.is_crossing_data = True

        with self.assertRaisesMessage(
            Exception,
            "The subwidgets operation needs to be one that returns only one object value.",
        ):
            get_source_data_from_widget(widget=self.widget_mock)
