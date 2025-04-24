from datetime import date

from django.utils import timezone
from django.utils.timezone import get_current_timezone_name
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from insights.utils import convert_date_str_to_datetime_date, convert_dt_to_localized_dt

MAX_ANALYTICS_DAYS_PERIOD_FILTER = 90
ANALYTICS_REQUIRED_FIELDS = ["waba_id", "template_id", "start_date", "end_date"]


def validate_analytics_kwargs(filters: dict, timezone_name: str | None = None) -> dict:
    if not timezone_name:
        timezone_name = get_current_timezone_name()

    analytics_kwargs = {k: None for k in ANALYTICS_REQUIRED_FIELDS}
    missing_fields = []

    filters = filters.copy()

    if "date_start" in filters:
        filters["start_date"] = filters.pop("date_start")[0]

    if "date_end" in filters:
        filters["end_date"] = filters.pop("date_end")[0]

    for field in analytics_kwargs.keys():
        if field not in filters:
            missing_fields.append(field)

        analytics_kwargs[field] = filters.get(field)

    if missing_fields:
        raise ValidationError(
            {"error": f"Required fields are missing: {', '.join(missing_fields)}"},
            code="required_fields_missing",
        )

    for dt_field in ["start_date", "end_date"]:
        try:
            dt = convert_date_str_to_datetime_date(analytics_kwargs[dt_field])
        except ValueError as err:
            raise ValidationError(
                {
                    dt_field: "Invalid date format. Please provide the date in 'YYYY-MM-DD' format, e.g., '2025-12-25'."
                },
                code="invalid_date_format",
            ) from err

        analytics_kwargs[dt_field] = convert_dt_to_localized_dt(
            dt, timezone_name
        ).date()

    validate_analytics_selected_period(analytics_kwargs.get("start_date"))

    return analytics_kwargs


def validate_analytics_selected_period(
    start_date: date,
    field_name: str = "start_date",
):
    if (timezone.now().date() - start_date).days > MAX_ANALYTICS_DAYS_PERIOD_FILTER:
        raise ValidationError(
            {field_name: "Start must be within the query period of the last 90 days."}
        )


def validate_list_templates_filters(filters: dict):
    if not filters.get("waba_id", None):
        raise ValidationError(
            {"error": _("WABA id is required")}, code="waba_id_missing"
        )

    allowed_filters = [
        "waba_id",
        "name",
        "limit",
        "before",
        "after",
        "language",
        "category",
        "search",
        "fields",
    ]
    valid_filters = {}

    for filter_name in allowed_filters:
        if filter_name in filters:
            valid_filters[filter_name] = filters[filter_name]

    if "search" in filters:
        valid_filters["name"] = filters["search"]

    return valid_filters
