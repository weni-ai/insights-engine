import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from insights.sources.base import BaseQueryExecutor
from insights.sources.services import DataSourceService
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class FakeQueryExecutor(BaseQueryExecutor):
    @classmethod
    def execute(cls, *args, **kwargs):
        return {"result": "data"}


def _make_widget(
    widget_type="default",
    source_slug="rooms",
    widget_name="test_widget",
    vtex_account=None,
    is_crossing_data=False,
):
    project = MagicMock()
    project.uuid = uuid.uuid4()
    project.vtex_account = vtex_account
    project.timezone = "America/Sao_Paulo"

    source = MagicMock()
    source.slug = source_slug

    widget = MagicMock()
    widget.type = widget_type
    widget.name = widget_name
    widget.source = source
    widget.project = project
    widget.is_crossing_data = is_crossing_data
    widget.config = {}

    return widget


class TestDataSourceServiceGetSourceQueryExecutor(TestCase):
    def test_delegates_to_factory(self):
        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        result = service.get_source_query_executor("rooms")

        self.assertEqual(result, FakeQueryExecutor)
        mock_factory.get_source_query_executor.assert_called_once_with("rooms")


class TestDataSourceServiceHandleSerializedAuth(TestCase):
    def test_returns_empty_dict_for_non_vtex_widget(self):
        service = DataSourceService()
        widget = _make_widget(widget_type="default")

        result = service._handle_serialized_auth(widget)

        self.assertEqual(result, {})

    @patch("insights.sources.services.JWTService")
    def test_returns_auth_with_vtex_account(self, MockJWTService):
        mock_jwt = MockJWTService.return_value
        mock_jwt.generate_jwt_token.return_value = "test-jwt-token"

        service = DataSourceService()
        widget = _make_widget(
            widget_type="vtex_order",
            vtex_account="my-vtex-store",
        )

        result = service._handle_serialized_auth(widget)

        self.assertEqual(result["domain"], "my-vtex-store")
        self.assertEqual(result["internal_token"], "test-jwt-token")
        mock_jwt.generate_jwt_token.assert_called_once_with(
            vtex_account="my-vtex-store"
        )

    def test_falls_back_to_vtexcredentials_executor(self):
        mock_auth_executor = MagicMock()
        mock_auth_executor.execute.return_value = {
            "domain": "store-from-creds",
            "internal_token": "creds-token",
        }

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = mock_auth_executor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(widget_type="vtex_order", vtex_account=None)

        result = service._handle_serialized_auth(widget)

        self.assertEqual(result["domain"], "store-from-creds")
        mock_factory.get_source_query_executor.assert_called_with("vtexcredentials")

    def test_raises_permission_denied_when_credentials_not_found(self):
        mock_auth_executor = MagicMock()
        mock_auth_executor.execute.side_effect = VtexCredentialsNotFound()

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = mock_auth_executor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(widget_type="vtex_order", vtex_account=None)

        with self.assertRaises(PermissionDenied):
            service._handle_serialized_auth(widget)


class TestDataSourceServiceGetExtraQueryKwargs(TestCase):
    def test_returns_timeseries_kwargs_for_peaks_widget(self):
        service = DataSourceService()
        widget = _make_widget(
            widget_name="human_service_dashboard.peaks_in_human_service"
        )

        result = service._get_extra_query_kwargs(widget, is_report=False)

        self.assertEqual(
            result["timeseries_hour_kwargs"],
            {"start_hour": 7, "end_hour": 18},
        )

    def test_returns_empty_dict_for_peaks_widget_as_report(self):
        service = DataSourceService()
        widget = _make_widget(
            widget_name="human_service_dashboard.peaks_in_human_service"
        )

        result = service._get_extra_query_kwargs(widget, is_report=True)

        self.assertEqual(result, {})

    def test_returns_empty_dict_for_other_widgets(self):
        service = DataSourceService()
        widget = _make_widget(widget_name="some_other_widget")

        result = service._get_extra_query_kwargs(widget, is_report=False)

        self.assertEqual(result, {})


class TestDataSourceServiceGetSourceDataFromWidget(TestCase):
    @patch("insights.sources.services.simple_source_data_operation")
    def test_calls_simple_operation_for_non_crossing_widget(self, mock_simple_op):
        mock_simple_op.return_value = {"value": 42}

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(is_crossing_data=False)

        result = service.get_source_data_from_widget(
            widget=widget,
            filters={"date__gte": "2025-01-01"},
            user_email="test@test.com",
        )

        self.assertEqual(result, {"value": 42})
        mock_simple_op.assert_called_once()
        call_kwargs = mock_simple_op.call_args[1]
        self.assertEqual(call_kwargs["source_query"], FakeQueryExecutor)
        self.assertFalse(call_kwargs["is_live"])
        self.assertEqual(call_kwargs["user_email"], "test@test.com")

    @patch("insights.sources.services.cross_source_data_operation")
    def test_calls_cross_operation_for_crossing_widget(self, mock_cross_op):
        mock_cross_op.return_value = {"value": 50}

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(is_crossing_data=True)

        result = service.get_source_data_from_widget(widget=widget)

        self.assertEqual(result, {"value": 50})
        mock_cross_op.assert_called_once()

    @patch("insights.sources.services.simple_source_data_operation")
    def test_uses_report_when_is_report_is_true(self, mock_simple_op):
        mock_simple_op.return_value = {"value": 10}

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget()
        report_widget = MagicMock()
        report_widget.type = "default"
        report_widget.name = "report"
        report_widget.is_crossing_data = False
        report_widget.project = widget.project
        widget.report = report_widget

        result = service.get_source_data_from_widget(widget=widget, is_report=True)

        self.assertEqual(result, {"value": 10})
        call_kwargs = mock_simple_op.call_args[1]
        self.assertEqual(call_kwargs["widget"], report_widget)

    def test_raises_exception_when_source_not_found(self):
        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = None

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget()

        with self.assertRaises(Exception) as ctx:
            service.get_source_data_from_widget(widget=widget)

        self.assertIn("could not find a source", str(ctx.exception))

    @patch("insights.sources.services.simple_source_data_operation")
    def test_passes_vtex_auth_params(self, mock_simple_op):
        mock_simple_op.return_value = {"orders": []}

        mock_auth_executor = MagicMock()
        mock_auth_executor.execute.return_value = {
            "domain": "vtex-store",
            "internal_token": "jwt-token",
        }

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.side_effect = lambda name: (
            mock_auth_executor if name == "vtexcredentials" else FakeQueryExecutor
        )

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(widget_type="vtex_order", vtex_account=None)

        service.get_source_data_from_widget(widget=widget)

        call_kwargs = mock_simple_op.call_args[1]
        self.assertEqual(call_kwargs["auth_params"]["domain"], "vtex-store")

    @patch("insights.sources.services.simple_source_data_operation")
    def test_passes_extra_query_kwargs_for_peaks_widget(self, mock_simple_op):
        mock_simple_op.return_value = {"results": []}

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget(
            widget_name="human_service_dashboard.peaks_in_human_service"
        )

        service.get_source_data_from_widget(widget=widget, is_report=False)

        call_kwargs = mock_simple_op.call_args[1]
        self.assertEqual(
            call_kwargs["extra_query_kwargs"]["timeseries_hour_kwargs"],
            {"start_hour": 7, "end_hour": 18},
        )

    @patch("insights.sources.services.simple_source_data_operation")
    def test_defaults_filters_to_empty_dict_when_none(self, mock_simple_op):
        mock_simple_op.return_value = {}

        mock_factory = MagicMock()
        mock_factory.get_source_query_executor.return_value = FakeQueryExecutor

        service = DataSourceService(source_query_executor_factory=mock_factory)
        widget = _make_widget()

        service.get_source_data_from_widget(widget=widget, filters=None)

        call_kwargs = mock_simple_op.call_args[1]
        self.assertEqual(call_kwargs["filters"], {})
