from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from insights.metrics.meta.validators import (
    MAX_ANALYTICS_DAYS_PERIOD_FILTER,
    validate_analytics_kwargs,
    validate_analytics_optional_fields,
    validate_analytics_selected_period,
    validate_list_templates_filters,
)


class ValidateAnalyticsOptionalFieldsTestCase(TestCase):
    def test_returns_none_product_type_when_not_provided(self):
        result = validate_analytics_optional_fields({})

        self.assertEqual(result, {"product_type": None})

    def test_accepts_cloud_api_product_type(self):
        result = validate_analytics_optional_fields({"product_type": "CLOUD_API"})

        self.assertEqual(result, {"product_type": "CLOUD_API"})

    def test_accepts_mm_lite_product_type(self):
        result = validate_analytics_optional_fields(
            {"product_type": "MARKETING_MESSAGES_LITE_API"}
        )

        self.assertEqual(
            result, {"product_type": "MARKETING_MESSAGES_LITE_API"}
        )

    def test_rejects_invalid_product_type(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_optional_fields({"product_type": "INVALID"})

        self.assertEqual(ctx.exception.get_codes(), {"error": "invalid_product_type"})


class ValidateAnalyticsSelectedPeriodTestCase(TestCase):
    def test_accepts_start_date_within_period(self):
        start = timezone.now().date() - timedelta(days=10)

        self.assertIsNone(validate_analytics_selected_period(start))

    def test_accepts_start_date_at_exact_limit(self):
        start = timezone.now().date() - timedelta(
            days=MAX_ANALYTICS_DAYS_PERIOD_FILTER
        )

        self.assertIsNone(validate_analytics_selected_period(start))

    def test_rejects_start_date_older_than_max_period(self):
        start = timezone.now().date() - timedelta(
            days=MAX_ANALYTICS_DAYS_PERIOD_FILTER + 1
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_selected_period(start)

        self.assertIn("start_date", ctx.exception.detail)

    def test_uses_custom_field_name_in_error(self):
        start = timezone.now().date() - timedelta(
            days=MAX_ANALYTICS_DAYS_PERIOD_FILTER + 1
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_selected_period(start, field_name="date_start")

        self.assertIn("date_start", ctx.exception.detail)


class ValidateAnalyticsKwargsTestCase(TestCase):
    def _valid_filters(self):
        today = timezone.now().date()
        start = today - timedelta(days=10)
        end = today
        return {
            "waba_id": "waba-1",
            "template_id": "tpl-1",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
        }

    def test_returns_kwargs_when_filters_are_valid(self):
        result = validate_analytics_kwargs(self._valid_filters())

        self.assertEqual(result["waba_id"], "waba-1")
        self.assertEqual(result["template_id"], "tpl-1")
        self.assertIsInstance(result["start_date"], date)
        self.assertIsInstance(result["end_date"], date)
        self.assertIsNone(result["product_type"])

    def test_includes_product_type_when_provided(self):
        filters = self._valid_filters()
        filters["product_type"] = "CLOUD_API"

        result = validate_analytics_kwargs(filters)

        self.assertEqual(result["product_type"], "CLOUD_API")

    def test_raises_when_required_fields_are_missing(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_kwargs({"waba_id": "waba-1"})

        self.assertEqual(
            ctx.exception.get_codes(), {"error": "required_fields_missing"}
        )

    def test_raises_for_invalid_date_format(self):
        filters = self._valid_filters()
        filters["start_date"] = "15/01/2025"

        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_kwargs(filters)

        self.assertIn("start_date", ctx.exception.detail)
        self.assertEqual(
            ctx.exception.get_codes().get("start_date"), "invalid_date_format"
        )

    def test_raises_for_invalid_end_date_format(self):
        filters = self._valid_filters()
        filters["end_date"] = "not-a-date"

        with self.assertRaises(ValidationError) as ctx:
            validate_analytics_kwargs(filters)

        self.assertIn("end_date", ctx.exception.detail)

    def test_raises_when_start_date_too_old(self):
        today = timezone.now().date()
        filters = {
            "waba_id": "waba-1",
            "template_id": "tpl-1",
            "start_date": (
                today - timedelta(days=MAX_ANALYTICS_DAYS_PERIOD_FILTER + 5)
            ).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
        }

        with self.assertRaises(ValidationError):
            validate_analytics_kwargs(filters)

    def test_accepts_date_start_and_date_end_aliases(self):
        today = timezone.now().date()
        start = today - timedelta(days=5)
        end = today
        filters = {
            "waba_id": "waba-1",
            "template_id": "tpl-1",
            "date_start": [start.strftime("%Y-%m-%d")],
            "date_end": [end.strftime("%Y-%m-%d")],
        }

        result = validate_analytics_kwargs(filters)

        self.assertIsInstance(result["start_date"], date)
        self.assertIsInstance(result["end_date"], date)

    def test_does_not_mutate_original_filters(self):
        filters = self._valid_filters()
        original = filters.copy()

        validate_analytics_kwargs(filters)

        self.assertEqual(filters, original)

    def test_uses_provided_timezone_name(self):
        filters = self._valid_filters()

        with patch(
            "insights.metrics.meta.validators.convert_dt_to_localized_dt"
        ) as mock_convert:
            mock_convert.side_effect = lambda dt, tz: datetime(
                dt.year, dt.month, dt.day, tzinfo=dt_timezone.utc
            )

            validate_analytics_kwargs(filters, timezone_name="America/Sao_Paulo")

        for call_args in mock_convert.call_args_list:
            self.assertEqual(call_args.args[1], "America/Sao_Paulo")


class ValidateListTemplatesFiltersTestCase(TestCase):
    def test_raises_when_waba_id_is_missing(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_list_templates_filters({})

        self.assertEqual(ctx.exception.get_codes(), {"error": "waba_id_missing"})

    def test_returns_only_allowed_filters(self):
        filters = {
            "waba_id": "waba-1",
            "name": "tpl",
            "limit": 10,
            "before": "cursor-a",
            "after": "cursor-b",
            "language": "pt_BR",
            "category": "MARKETING",
            "fields": "name,status",
            "unknown_field": "should-be-removed",
        }

        result = validate_list_templates_filters(filters)

        self.assertNotIn("unknown_field", result)
        self.assertEqual(result["waba_id"], "waba-1")
        self.assertEqual(result["name"], "tpl")
        self.assertEqual(result["limit"], 10)
        self.assertEqual(result["before"], "cursor-a")
        self.assertEqual(result["after"], "cursor-b")
        self.assertEqual(result["language"], "pt_BR")
        self.assertEqual(result["category"], "MARKETING")
        self.assertEqual(result["fields"], "name,status")

    def test_search_overrides_name_filter(self):
        filters = {"waba_id": "waba-1", "name": "old", "search": "new"}

        result = validate_list_templates_filters(filters)

        self.assertEqual(result["name"], "new")
        self.assertEqual(result["search"], "new")

    def test_returns_minimal_filters_when_only_waba_id_provided(self):
        result = validate_list_templates_filters({"waba_id": "waba-1"})

        self.assertEqual(result, {"waba_id": "waba-1"})
