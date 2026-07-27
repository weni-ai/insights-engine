from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from insights.projects.models import Project


def to_utc_range(
    start_date: date, end_date: date, project: Project
) -> tuple[datetime, datetime]:
    """
    Convert calendar dates to a UTC datetime range using the project's timezone.

    Start is local midnight; end is local 23:59:59. Both are returned in UTC so
    VTEX authorizedDate filters include the full local days selected by the user.
    """
    project_tz = ZoneInfo(project.timezone) if project.timezone else ZoneInfo("UTC")
    start_local = datetime.combine(start_date, time.min, tzinfo=project_tz)
    end_local = datetime.combine(end_date, time(23, 59, 59), tzinfo=project_tz)
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )
