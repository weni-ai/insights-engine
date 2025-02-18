from insights.metrics.skills.exceptions import InvalidDateFormat
from insights.utils import convert_date_str_to_datetime_date


def validate_date_str(date_str: str):
    try:
        return convert_date_str_to_datetime_date(date_str)
    except ValueError as e:
        raise InvalidDateFormat("Invalid date format. Should be YYYY-MM-DD.") from e
