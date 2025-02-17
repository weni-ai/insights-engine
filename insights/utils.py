from datetime import date, datetime
import pytz
from insights.authentication.authentication import FlowsInternalAuthentication


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


def convert_date_to_unix_timestamp(dt: date) -> int:
    return int(datetime.combine(dt, datetime.min.time()).timestamp())


def convert_date_str_to_datetime_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_token_flows_authentication(project_uuid, user_email):
    response_token = FlowsInternalAuthentication().get_flows_user_api_token(
        project_uuid, user_email
    )

    token_data = response_token.json()
    api_token = token_data.get("api_token")

    return api_token
