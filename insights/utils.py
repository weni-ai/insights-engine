import logging
from datetime import date, datetime

import pytz

from insights.authentication.authentication import FlowsInternalAuthentication

logger = logging.getLogger(__name__)


def format_to_iso_utc(date_str, end_of_day=False):
    """Converte uma string de data para o formato ISO 8601.
    Se `end_of_day` for True, adiciona T23:59:58Z, senão adiciona T00:00:00Z."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=58, tzinfo=pytz.UTC)
        else:
            dt = dt.replace(hour=0, minute=0, second=0, tzinfo=pytz.UTC)

        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    except ValueError:
        return None
    except Exception as e:
        logger.error(f"Unexpected error in date formatting: {e}")
        return None


def convert_date_to_unix_timestamp(
    dt: date,
    use_max_time=False,
) -> int:
    t = datetime.max.time() if use_max_time else datetime.min.time()

    return int(datetime.combine(dt, t).timestamp())


def convert_date_str_to_datetime_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_token_flows_authentication(project_uuid, user_email):
    response_token = FlowsInternalAuthentication().get_flows_user_api_token(
        project_uuid, user_email
    )

    token_data = response_token.json()
    api_token = token_data.get("api_token")

    return api_token


def convert_dt_to_localized_dt(dt: datetime, timezone_name: str) -> datetime:
    tz = pytz.timezone(timezone_name)

    # Get the current time in that timezone
    now = datetime.now(tz=tz)
    local_time = now.time()

    # Combine the given date with the current local time
    combined_local_dt = datetime.combine(dt, local_time)

    # Localize the combined datetime to the given timezone
    localized_dt = tz.localize(combined_local_dt)

    # Convert to UTC
    dt_utc = localized_dt.astimezone(pytz.utc)

    return dt_utc
