from datetime import date
from rest_framework.exceptions import ValidationError

from insights.utils import convert_date_str_to_datetime_date

MAX_ANALYTICS_DAYS_PERIOD_FILTER = 90


def validate_analytics_kwargs(filters: dict) -> dict:
    analytics_kwargs = {
        k: None for k in ["waba_id", "template_id", "start_date", "end_date"]
    }
    missing_fields = []

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
            analytics_kwargs[dt_field] = convert_date_str_to_datetime_date(
                analytics_kwargs[dt_field]
            )
        except ValueError as err:
            raise ValidationError(
                {
                    dt_field: "Invalid date format. Please provide the date in 'YYYY-MM-DD' format, e.g., '2025-12-25'."
                },
                code="invalid_date_format",
            ) from err

    validate_analytics_selected_period(
        analytics_kwargs.get("start_date"), analytics_kwargs.get("end_date")
    )

    return analytics_kwargs


def validate_analytics_selected_period(start_date: date, end_date: date):
    if (end_date - start_date).days > MAX_ANALYTICS_DAYS_PERIOD_FILTER:
        raise ValidationError(
            {"start_date": "Start must be within the query period of the last 90 days."}
        )