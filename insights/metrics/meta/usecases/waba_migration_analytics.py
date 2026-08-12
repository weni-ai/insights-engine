from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

from sentry_sdk import capture_exception

from insights.dashboards.models import Dashboard
from insights.metrics.meta.enums import ProductType

logger = logging.getLogger(__name__)

MESSAGE_STATUS_KEYS = ("sent", "delivered", "read", "clicked")
DEFAULT_PRODUCT_TYPES = (
    ProductType.CLOUD_API.value,
    ProductType.MM_LITE.value,
)


def resolve_product_types(product_type: str | None) -> list[str]:
    """
    Resolve which Meta product_type values to query.

    When product_type is omitted, fetch Cloud API and MM Lite so the dashboard
    no longer needs a data-source filter.
    """
    if product_type:
        return [product_type]
    return list(DEFAULT_PRODUCT_TYPES)


@dataclass(frozen=True)
class WabaAnalyticsPeriod:
    """One Meta analytics request for a specific WABA and date range."""

    waba_id: str
    start_date: date | datetime
    end_date: date | datetime
    template_id: str | None = None


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
    - days strictly before migrated_at → old WABA only
    - any range that includes migrated_at or later → query old for the FULL
      requested range AND current from migrated_at (or start) to end

    Traffic can keep landing on the old WABA after migrated_at (e.g. delayed
    cutover, dual routing). Stopping the old query at migrated_at undercounts.
    Overlapping days are merged by summing; when the new WABA has no volume,
    the sum keeps the old WABA totals.

    The migration day is included in BOTH requests so morning traffic on the
    old WABA and afternoon traffic on the new one are both kept.

    Examples (migrated_at = 2026-03-15):
    - 03-01..03-10 → only old
    - 03-20..03-31 → old (03-20..03-31) + current (03-20..03-31)
    - 03-01..03-31 → old (03-01..03-31) + current (03-15..03-31)
    - 03-15..03-15 → old (03-15) + current (03-15)
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

    # Entire range is strictly before the migration day.
    if end < migrated_at:
        return [
            WabaAnalyticsPeriod(
                waba_id=old_waba_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]

    # Range reaches the migration day or later: keep querying the old WABA for
    # the full filter window (post-migration traffic may still land there),
    # and also query the current WABA from the cutover day onward.
    return [
        WabaAnalyticsPeriod(
            waba_id=old_waba_id,
            start_date=start,
            end_date=end,
        ),
        WabaAnalyticsPeriod(
            waba_id=current_waba_id,
            start_date=max(start, migrated_at),
            end_date=end,
        ),
    ]


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

    status_count = {status: {"value": value} for status, value in status_totals.items()}
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


def find_exact_template_id_by_name(
    templates_response: dict | list | None,
    template_name: str,
) -> str | None:
    """
    Pick the template whose name matches exactly from a Meta list response.

    Meta's name filter is a search, so similar names may appear; only an exact
    match is accepted.
    """
    if not template_name:
        return None

    if isinstance(templates_response, dict):
        templates = templates_response.get("data") or []
    elif isinstance(templates_response, list):
        templates = templates_response
    else:
        templates = []

    for template in templates:
        if not isinstance(template, dict):
            continue
        if template.get("name") == template_name and template.get("id"):
            return str(template["id"])

    return None


def resolve_old_template_id(
    meta_client,
    *,
    old_waba_id: str,
    new_template_id: str,
) -> str | None:
    """
    Resolve the equivalent template id on the old WABA from the new template name.

    Returns None when the cloned template does not exist on the old WABA
    (e.g. created after migration).
    """
    preview = meta_client.get_template_preview(template_id=new_template_id)
    template_name = (preview or {}).get("name") if isinstance(preview, dict) else None

    if not template_name:
        logger.info(
            "Could not resolve template name for template_id=%s when looking up "
            "equivalent on old_waba_id=%s; using new WABA analytics only",
            new_template_id,
            old_waba_id,
        )
        return None

    templates_response = meta_client.get_templates_list(
        waba_id=old_waba_id,
        name=template_name,
    )
    old_template_id = find_exact_template_id_by_name(templates_response, template_name)

    if not old_template_id:
        logger.info(
            "No exact template name match for name=%s on old_waba_id=%s "
            "(new_template_id=%s); using new WABA analytics only",
            template_name,
            old_waba_id,
            new_template_id,
        )
        return None

    return old_template_id


def extract_pricing_data_points(response: dict | None) -> list:
    """Extract pricing analytics data_points from a Meta Graph API response."""
    if not isinstance(response, dict):
        return []

    data = response.get("pricing_analytics", {}).get("data") or []
    if not data:
        return []

    first = data[0] if isinstance(data[0], dict) else {}
    return list(first.get("data_points") or [])


def merge_pricing_analytics_responses(responses: list[dict]) -> dict:
    """
    Merge Meta pricing_analytics responses by concatenating data_points.

    Aggregation by category happens later in ConversationsByCategoryAggregations.
    """
    all_points: list = []
    for response in responses:
        all_points.extend(extract_pricing_data_points(response))

    return {
        "pricing_analytics": {
            "data": [{"data_points": all_points}],
        }
    }


class ConsolidateWabaAnalyticsUseCase:
    """
    Intermediate layer between the service and the Meta client.

    Looks up migration_data, splits the date range when needed, resolves the
    equivalent old template id by name when querying the old WABA, calls Meta
    for each period, and returns one consolidated response.
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

    def get_conversations_by_category(
        self,
        *,
        waba_id: str,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> dict:
        """
        Fetch pricing analytics by category, splitting across WABAs when needed.

        Unlike template analytics, this endpoint is WABA-scoped and does not
        require template_id remapping.
        """
        periods = resolve_waba_analytics_periods(
            current_waba_id=waba_id,
            start_date=start_date,
            end_date=end_date,
        )

        responses = [
            self.meta_client.get_conversations_by_category(
                waba_id=period.waba_id,
                start_date=period.start_date,
                end_date=period.end_date,
            )
            for period in periods
        ]

        if len(responses) == 1:
            return responses[0]

        return merge_pricing_analytics_responses(responses)

    def _periods_with_template_ids(
        self,
        *,
        current_waba_id: str,
        new_template_id: str,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> list[WabaAnalyticsPeriod]:
        periods = resolve_waba_analytics_periods(
            current_waba_id=current_waba_id,
            start_date=start_date,
            end_date=end_date,
        )

        if len(periods) == 1 and periods[0].waba_id == current_waba_id:
            return [
                WabaAnalyticsPeriod(
                    waba_id=periods[0].waba_id,
                    start_date=periods[0].start_date,
                    end_date=periods[0].end_date,
                    template_id=new_template_id,
                )
            ]

        old_waba_ids = {
            period.waba_id for period in periods if period.waba_id != current_waba_id
        }
        old_template_id = None
        if old_waba_ids:
            old_waba_id = next(iter(old_waba_ids))
            old_template_id = resolve_old_template_id(
                self.meta_client,
                old_waba_id=old_waba_id,
                new_template_id=new_template_id,
            )

        resolved: list[WabaAnalyticsPeriod] = []
        for period in periods:
            if period.waba_id == current_waba_id:
                resolved.append(
                    WabaAnalyticsPeriod(
                        waba_id=period.waba_id,
                        start_date=period.start_date,
                        end_date=period.end_date,
                        template_id=new_template_id,
                    )
                )
                continue

            if not old_template_id:
                continue

            resolved.append(
                WabaAnalyticsPeriod(
                    waba_id=period.waba_id,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    template_id=old_template_id,
                )
            )

        if not resolved:
            # Fallback: only the current WABA with the requested range.
            return [
                WabaAnalyticsPeriod(
                    waba_id=current_waba_id,
                    start_date=start_date,
                    end_date=end_date,
                    template_id=new_template_id,
                )
            ]

        return resolved

    def _fetch_and_consolidate(
        self,
        *,
        fetch: Callable,
        merge: Callable[[list[dict]], dict],
        fetch_kwargs: dict,
    ) -> dict:
        fetch_kwargs = dict(fetch_kwargs)
        product_type = fetch_kwargs.pop("product_type", None) or None
        product_types = resolve_product_types(product_type)
        merging_both_sources = product_type is None

        periods = self._periods_with_template_ids(
            current_waba_id=fetch_kwargs["waba_id"],
            new_template_id=fetch_kwargs["template_id"],
            start_date=fetch_kwargs["start_date"],
            end_date=fetch_kwargs["end_date"],
        )

        responses: list[dict] = []
        for period in periods:
            for resolved_product_type in product_types:
                try:
                    responses.append(
                        fetch(
                            **{
                                **fetch_kwargs,
                                "waba_id": period.waba_id,
                                "template_id": period.template_id,
                                "start_date": period.start_date,
                                "end_date": period.end_date,
                                "product_type": resolved_product_type,
                            }
                        )
                    )
                except Exception as error:
                    # MM Lite may be unavailable for some WABAs; keep Cloud API data.
                    if (
                        merging_both_sources
                        and resolved_product_type == ProductType.MM_LITE.value
                    ):
                        capture_exception(error)
                        logger.warning(
                            "Failed to fetch analytics for waba_id=%s "
                            "product_type=%s; skipping this source. Error: %s",
                            period.waba_id,
                            resolved_product_type,
                            error,
                            exc_info=True,
                        )
                        continue
                    raise

        if not responses:
            return merge([])

        if len(responses) == 1:
            return responses[0]

        return merge(responses)
