from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from insights.metrics.vtex.enums import OrdersSumGranularity, WeekStartsOn
from insights.projects.models import Project

END_OF_DAY_TIME = time(23, 59, 59)

WEEKDAY_INDEX = {
    WeekStartsOn.MONDAY: 0,
    WeekStartsOn.TUESDAY: 1,
    WeekStartsOn.WEDNESDAY: 2,
    WeekStartsOn.THURSDAY: 3,
    WeekStartsOn.FRIDAY: 4,
    WeekStartsOn.SATURDAY: 5,
    WeekStartsOn.SUNDAY: 6,
}


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
    end_local = datetime.combine(end_date, END_OF_DAY_TIME, tzinfo=project_tz)
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def week_start(d: date, week_starts_on: str | WeekStartsOn) -> date:
    target = WEEKDAY_INDEX[WeekStartsOn(week_starts_on)]
    delta = (d.weekday() - target) % 7
    return d - timedelta(days=delta)


def period_key_for(
    d: date,
    granularity: str | OrdersSumGranularity,
    week_starts_on: str | WeekStartsOn,
) -> date:
    if OrdersSumGranularity(granularity) == OrdersSumGranularity.DAY:
        return d
    return week_start(d, week_starts_on)


def iter_period_keys(
    start_date: date,
    end_date: date,
    granularity: str | OrdersSumGranularity,
    week_starts_on: str | WeekStartsOn,
) -> list[date]:
    if OrdersSumGranularity(granularity) == OrdersSumGranularity.DAY:
        keys = []
        current = start_date
        while current <= end_date:
            keys.append(current)
            current += timedelta(days=1)
        return keys

    keys = []
    current = week_start(start_date, week_starts_on)
    while current <= end_date:
        keys.append(current)
        current += timedelta(days=7)
    return keys
