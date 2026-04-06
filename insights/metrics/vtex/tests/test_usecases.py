from datetime import date, datetime, timezone
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status

from insights.metrics.vtex.usecases.utm_source_metrics import UTMSourceMetricsUseCase
from insights.projects.models import Project
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class TestUTMSourceMetricsUseCaseToUtcRange(TestCase):
    def setUp(self):
        self.use_case = UTMSourceMetricsUseCase()

    def test_converts_date_range_to_utc_using_project_timezone(self):
        project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )

        start, end = self.use_case.to_utc_range(
            date(2023, 9, 1),
            date(2023, 9, 4),
            project,
        )

        self.assertEqual(
            start,
            datetime(2023, 9, 1, 3, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime(2023, 9, 5, 2, 59, 59, tzinfo=timezone.utc),
        )

    def test_defaults_to_utc_when_project_timezone_is_empty(self):
        project = Project.objects.create(name="Test Project", timezone=None)

        start, end = self.use_case.to_utc_range(
            date(2023, 9, 1),
            date(2023, 9, 2),
            project,
        )

        self.assertEqual(
            start,
            datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime(2023, 9, 2, 23, 59, 59, tzinfo=timezone.utc),
        )


@patch("insights.metrics.vtex.usecases.utm_source_metrics.OrdersService")
class TestUTMSourceMetricsUseCaseExecute(TestCase):
    def setUp(self):
        self.use_case = UTMSourceMetricsUseCase()
        self.project = Project.objects.create(
            name="Test Project",
            timezone="UTC",
        )

    def test_returns_200_and_orders_data_on_success(self, mock_orders_service_cls):
        expected = {
            "revenue": {"value": 50.21, "currency_code": "BRL"},
            "orders_placed": {"value": 2},
        }
        mock_orders_service_cls.return_value.get_metrics_from_utm_source.return_value = (
            expected
        )

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2023, 9, 1),
            date(2023, 9, 2),
        )

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(body, expected)
        mock_orders_service_cls.assert_called_once_with(self.project)
        call_kwargs = (
            mock_orders_service_cls.return_value.get_metrics_from_utm_source.call_args
        )
        utm_arg, filters = call_kwargs[0]
        self.assertEqual(utm_arg, "weniabandonedcart")
        self.assertEqual(filters["project_uuid"], str(self.project.uuid))
        self.assertEqual(
            filters["start_date"],
            datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            filters["end_date"],
            datetime(2023, 9, 2, 23, 59, 59, tzinfo=timezone.utc),
        )

    def test_returns_401_when_vtex_credentials_not_found(self, mock_orders_service_cls):
        mock_orders_service_cls.return_value.get_metrics_from_utm_source.side_effect = (
            VtexCredentialsNotFound()
        )

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2023, 9, 1),
            date(2023, 9, 2),
        )

        self.assertEqual(status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            body["error"],
            (
                "Unauthorized because VTEX credentials are not configured "
                "or are invalid for this project"
            ),
        )

    @patch("insights.metrics.vtex.usecases.utm_source_metrics.capture_exception")
    def test_returns_500_and_event_id_on_unexpected_error(
        self, mock_capture_exception, mock_orders_service_cls
    ):
        mock_capture_exception.return_value = "test-event-id"
        mock_orders_service_cls.return_value.get_metrics_from_utm_source.side_effect = (
            RuntimeError("upstream failure")
        )

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2023, 9, 1),
            date(2023, 9, 2),
        )

        self.assertEqual(status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(body["error"], "Failed to get metrics from UTM source")
        self.assertEqual(body["event_id"], "test-event-id")
        mock_capture_exception.assert_called_once()
