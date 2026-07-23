from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable

from insights.dashboards.models import Dashboard

MESSAGE_STATUS_KEYS = ("sent", "delivered", "read", "clicked")


@dataclass(frozen=True)
class WabaAnalyticsPeriod:
    """One Meta analytics request for a specific WABA and date range."""

    waba_id: str
    start_date: date | datetime
    end_date: date | datetime


def get_migration_data_for_waba(waba_id: str) -> dict | None:
    """
    Return migration_data from the active WhatsApp dashboard for this waba_id.

    Expected shape:
        {"waba_id": "<old_waba_id>", "migrated_at": "<iso-utc>"}
    """
    dashboard = Dashboard.objects.filter(
        config__waba_id=waba_id,
        config__is_whatsapp_integration=True,
    ).first()

    if not dashboard or not isinstance(dashboard.config, dict):
        return None

    migration_data = dashboard.config.get("migration_data")
    if not isinstance(migration_data, dict):
        return None

    if not migration_data.get("waba_id") or not migration_data.get("migrated_at"):
        return None

    return migration_data


def _parse_migrated_at(migrated_at: str) -> date:
    normalized = migrated_at.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).date()


def _as_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def resolve_waba_analytics_periods(
    current_waba_id: str,
    start_date: date | datetime,
    end_date: date | datetime,
    migration_data: dict | None = None,
) -> list[WabaAnalyticsPeriod]:
    """
    Decide which WABA(s) to query based on the requested range and migration cutover.

    Cutover rule (migrated_at date in UTC):
    - days before migrated_at → old WABA
    - migrated_at and after → current WABA

    Examples (migrated_at = 2026-03-15):
    - 03-01..03-10 → only old
    - 03-20..03-31 → only current
    - 03-01..03-31 → old (03-01..03-14) + current (03-15..03-31)
    """
    start = _as_date(start_date)
    end = _as_date(end_date)

    if migration_data is None:
        migration_data = get_migration_data_for_waba(current_waba_id)

    if not migration_data:
        return [
            WabaAnalyticsPeriod(
                waba_id=current_waba_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]

    old_waba_id = migration_data["waba_id"]
    migrated_at = _parse_migrated_at(migration_data["migrated_at"])

    # Entire range is before the migration day.
    if end < migrated_at:
        return [
            WabaAnalyticsPeriod(
                waba_id=old_waba_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]

    # Entire range is on/after the migration day.
    if start >= migrated_at:
        return [
            WabaAnalyticsPeriod(
                waba_id=current_waba_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]

    # Range crosses the cutover: split into old + current periods.
    periods: list[WabaAnalyticsPeriod] = []
    old_end = migrated_at - timedelta(days=1)

    if start <= old_end:
        periods.append(
            WabaAnalyticsPeriod(
                waba_id=old_waba_id,
                start_date=start,
                end_date=old_end,
            )
        )

    periods.append(
        WabaAnalyticsPeriod(
            waba_id=current_waba_id,
            start_date=migrated_at,
            end_date=end,
        )
    )
    return periods


def _recalculate_status_percentages(status_count: dict) -> dict:
    sent = status_count["sent"]["value"]
    for status in ("delivered", "read", "clicked"):
        status_count[status]["percentage"] = (
            round((status_count[status]["value"] / sent) * 100, 2) if sent > 0 else 0
        )
    return status_count


def merge_messages_analytics(
    responses: list[dict],
    include_data_points: bool = True,
) -> dict:
    """Sum status_count values and data_points by date from multiple Meta responses."""
    status_totals = {status: 0 for status in MESSAGE_STATUS_KEYS}
    points_by_date: dict[str, dict] = {}

    for response in responses:
        data = response.get("data") or {}

        status_count = data.get("status_count") or {}
        for status in MESSAGE_STATUS_KEYS:
            status_totals[status] += status_count.get(status, {}).get("value", 0)

        if not include_data_points:
            continue

        for point in data.get("data_points") or []:
            point_date = point.get("date")
            if not point_date:
                continue

            merged = points_by_date.setdefault(
                point_date,
                {"date": point_date, **{status: 0 for status in MESSAGE_STATUS_KEYS}},
            )
            for status in MESSAGE_STATUS_KEYS:
                merged[status] += point.get(status, 0)

    status_count = {
        status: {"value": value} for status, value in status_totals.items()
    }
    result = {
        "data": {
            "status_count": _recalculate_status_percentages(status_count),
        }
    }

    if include_data_points:
        result["data"]["data_points"] = [
            points_by_date[key] for key in sorted(points_by_date.keys())
        ]

    return result


def merge_buttons_analytics(responses: list[dict]) -> dict:
    """
    Merge button analytics by label.

    Meta responses only expose click totals and click_rate (not sent).
    We reverse sent from click_rate so the consolidated click_rate stays coherent:
        estimated_sent = total * 100 / click_rate
    """
    buttons_by_label: dict[str, dict] = {}
    estimated_sent = 0.0

    for response in responses:
        for button in response.get("data") or []:
            label = button.get("label")
            if label is None:
                continue

            total = button.get("total", 0) or 0
            click_rate = button.get("click_rate", 0) or 0

            if click_rate > 0:
                estimated_sent += total * 100 / click_rate

            merged = buttons_by_label.setdefault(
                label,
                {"label": label, "type": button.get("type"), "total": 0},
            )
            merged["total"] += total
            if not merged.get("type") and button.get("type"):
                merged["type"] = button.get("type")

    merged_buttons = []
    for button in buttons_by_label.values():
        click_rate = (
            0
            if estimated_sent == 0
            else round((button["total"] / estimated_sent) * 100, 2)
        )
        merged_buttons.append(
            {
                "label": button["label"],
                "type": button.get("type"),
                "total": button["total"],
                "click_rate": click_rate,
            }
        )

    return {"data": merged_buttons}


class ConsolidateWabaAnalyticsUseCase:
    """
    Intermediate layer between the service and the Meta client.

    Looks up migration_data, splits the date range when needed, calls Meta for
    each period, and returns one consolidated response.
    """

    def __init__(self, meta_client):
        self.meta_client = meta_client

    def get_messages_analytics(self, *, include_data_points: bool = True, **kwargs):
        return self._fetch_and_consolidate(
            fetch=self.meta_client.get_messages_analytics,
            merge=lambda responses: merge_messages_analytics(
                responses, include_data_points=include_data_points
            ),
            fetch_kwargs={**kwargs, "include_data_points": include_data_points},
        )

    def get_buttons_analytics(self, **kwargs):
        return self._fetch_and_consolidate(
            fetch=self.meta_client.get_buttons_analytics,
            merge=merge_buttons_analytics,
            fetch_kwargs=kwargs,
        )

    def _fetch_and_consolidate(
        self,
        *,
        fetch: Callable,
        merge: Callable[[list[dict]], dict],
        fetch_kwargs: dict,
    ) -> dict:
        periods = resolve_waba_analytics_periods(
            current_waba_id=fetch_kwargs["waba_id"],
            start_date=fetch_kwargs["start_date"],
            end_date=fetch_kwargs["end_date"],
        )

        responses = [
            fetch(
                **{
                    **fetch_kwargs,
                    "waba_id": period.waba_id,
                    "start_date": period.start_date,
                    "end_date": period.end_date,
                }
            )
            for period in periods
        ]

        if len(responses) == 1:
            return responses[0]

        return merge(responses)
