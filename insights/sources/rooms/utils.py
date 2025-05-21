from datetime import date, datetime

import pytz
from pytz.tzinfo import BaseTzInfo


def convert_date_to_datetime(
    dt: date, use_max_time: bool = False, tz: BaseTzInfo = pytz.UTC
):
    """
    Convert a date to a datetime object.
    """
    t = datetime.max.time() if use_max_time else datetime.min.time()
    combined_dt = datetime.combine(dt, t)

    return tz.localize(combined_dt)


def adjust_date_filters(filters: dict, timezone_name: str):
    """
    Adjust the date filters to be used in the query.
    """
    tz = pytz.timezone(timezone_name) or pytz.UTC

    for name, value in filters.items():
        if name == "created_on__gte":
            use_max_time = False
        elif name == "created_on__lte":
            use_max_time = True
        else:
            continue

        try:
            new_value = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            continue

        dt = convert_date_to_datetime(new_value.date(), use_max_time, tz)
        filters[name] = dt.isoformat()

    return filters
