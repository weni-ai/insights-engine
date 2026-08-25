from datetime import date, datetime, time, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework import status

from insights.metrics.vtex.date_utils import END_OF_DAY_TIME, to_utc_range
from insights.metrics.vtex.enums import OrdersSumGranularity, WeekStartsOn
from insights.metrics.vtex.usecases.order_values_by_period import (
    OrderValuesByPeriodUseCase,
)
from insights.metrics.vtex.usecases.utm_source_metrics import UTMSourceMetricsUseCase
from insights.projects.models import Project
from insights.sources.orders.exceptions import VTEXOrdersAPIError
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class TestUTMSourceMetricsUseCaseToUtcRange(TestCase):
    def setUp(self):
        self.use_case = UTMSourceMetricsUseCase()

    def test_converts_date_range_to_utc_using_project_timezone(self):
        project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )
        start_date = date(2023, 9, 1)
        end_date = date(2023, 9, 4)
        project_tz = ZoneInfo(project.timezone)

        start, end = self.use_case.to_utc_range(start_date, end_date, project)

        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(end.tzinfo, timezone.utc)
        self.assertEqual(start.astimezone(project_tz).date(), start_date)
        self.assertEqual(start.astimezone(project_tz).time(), time.min)
        self.assertEqual(end.astimezone(project_tz).date(), end_date)
        self.assertEqual(end.astimezone(project_tz).time(), END_OF_DAY_TIME)

    def test_defaults_to_utc_when_project_timezone_is_empty(self):
        project = Project.objects.create(name="Test Project", timezone=None)
        start_date = date(2023, 9, 1)
        end_date = date(2023, 9, 2)

        start, end = self.use_case.to_utc_range(start_date, end_date, project)

        self.assertEqual(
            start,
            datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        )
        self.assertEqual(
            end,
            datetime.combine(end_date, END_OF_DAY_TIME, tzinfo=timezone.utc),
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
        expected_start, expected_end = to_utc_range(
            date(2023, 9, 1),
            date(2023, 9, 2),
            self.project,
        )
        self.assertEqual(filters["start_date"], expected_start)
        self.assertEqual(filters["end_date"], expected_end)

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


@patch("insights.metrics.vtex.usecases.order_values_by_period.OrdersService")
class TestOrderValuesByPeriodUseCaseExecute(TestCase):
    def setUp(self):
        self.use_case = OrderValuesByPeriodUseCase()
        self.project = Project.objects.create(
            name="Test Project",
            timezone="UTC",
        )

    def test_returns_grouped_values_by_day_with_zero_fill(
        self, mock_orders_service_cls
    ):
        mock_orders_service_cls.return_value.get_orders_from_utm_source.return_value = {
            "currency_code": "BRL",
            "orders": [
                {
                    "authorized_date": "2026-08-01T12:00:00.000Z",
                    "total_value": 20000,
                    "currency_code": "BRL",
                },
                {
                    "authorized_date": "2026-08-01T18:00:00.000Z",
                    "total_value": 10000,
                    "currency_code": "BRL",
                },
                {
                    "authorized_date": "2026-08-10T10:00:00.000Z",
                    "total_value": 52010,
                    "currency_code": "BRL",
                },
            ],
        }

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2026, 8, 1),
            date(2026, 8, 3),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(body["currency"], "BRL")
        self.assertEqual(
            body["results"],
            [
                {"2026-08-01": {"value": 300.0}},
                {"2026-08-02": {"value": 0.0}},
                {"2026-08-03": {"value": 0.0}},
            ],
        )

    def test_returns_grouped_values_by_week_using_week_start(
        self, mock_orders_service_cls
    ):
        mock_orders_service_cls.return_value.get_orders_from_utm_source.return_value = {
            "currency_code": "BRL",
            "orders": [
                {
                    "authorized_date": "2026-08-01T12:00:00.000Z",
                    "total_value": 30000,
                    "currency_code": "BRL",
                },
                {
                    "authorized_date": "2026-08-10T10:00:00.000Z",
                    "total_value": 52010,
                    "currency_code": "BRL",
                },
            ],
        }

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2026, 8, 1),
            date(2026, 8, 14),
            OrdersSumGranularity.WEEK,
            WeekStartsOn.SUNDAY,
        )

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(
            body["results"],
            [
                {"2026-07-26": {"value": 300.0}},
                {"2026-08-02": {"value": 0.0}},
                {"2026-08-09": {"value": 520.1}},
            ],
        )

    def test_returns_null_currency_and_zeros_when_there_are_no_orders(
        self, mock_orders_service_cls
    ):
        mock_orders_service_cls.return_value.get_orders_from_utm_source.return_value = {
            "currency_code": None,
            "orders": [],
        }

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2026, 8, 1),
            date(2026, 8, 2),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertIsNone(body["currency"])
        self.assertEqual(
            body["results"],
            [
                {"2026-08-01": {"value": 0.0}},
                {"2026-08-02": {"value": 0.0}},
            ],
        )

    def test_returns_401_when_vtex_credentials_not_found(self, mock_orders_service_cls):
        mock_orders_service_cls.return_value.get_orders_from_utm_source.side_effect = (
            VtexCredentialsNotFound()
        )

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2026, 8, 1),
            date(2026, 8, 2),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )

        self.assertEqual(status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            body["error"],
            (
                "Unauthorized because VTEX credentials are not configured "
                "or are invalid for this project"
            ),
        )

    @patch("insights.metrics.vtex.usecases.order_values_by_period.capture_exception")
    def test_returns_500_and_event_id_on_vtex_api_error(
        self, mock_capture_exception, mock_orders_service_cls
    ):
        mock_capture_exception.return_value = "test-event-id"
        mock_orders_service_cls.return_value.get_orders_from_utm_source.side_effect = (
            VTEXOrdersAPIError("upstream failure")
        )

        status_code, body = self.use_case.execute(
            self.project,
            "weniabandonedcart",
            date(2026, 8, 1),
            date(2026, 8, 2),
            OrdersSumGranularity.DAY,
            WeekStartsOn.SUNDAY,
        )

        self.assertEqual(status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(body["error"], "Failed to get order values by period")
        self.assertEqual(body["event_id"], "test-event-id")
        mock_capture_exception.assert_called_once()
