from datetime import datetime
import pytz


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
