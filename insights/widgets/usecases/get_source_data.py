from datetime import datetime, time

import pytz

from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source
from insights.widgets.models import Widget


def verify_filters(default_filters: dict):
    print("filtros", default_filters)
    if "created_on__gte" in default_filters.get(
        "filter", {}
    ) and "created_on__lte" in default_filters.get("filter", {}):
        if "ended_at__gte" in default_filters.get("filter", {}):
            del default_filters["ended_at__gte"]


def set_live_day(default_filters: dict, key: str):
    start_of_day = datetime.combine(datetime.now().date(), time.min)
    default_filters[key] = start_of_day


def apply_timezone_to_date_filters(default_filters: dict, timezone: str):
    tz = pytz.timezone(timezone)
    date_suffixes = ["__gte", "__lte"]

    for key, value in list(default_filters.items()):
        if any(key.endswith(suffix) for suffix in date_suffixes):
            if value == "today":
                set_live_day(default_filters, key)
                value = default_filters[key]

            if isinstance(value, str):
                date_value = datetime.strptime(value, "%Y-%m-%d")
                default_filters[key] = tz.localize(date_value)
            elif isinstance(value, datetime):
                default_filters[key] = tz.localize(value)


def get_source_data_from_widget(
    widget: Widget, is_report: bool = False, filters: dict = {}, user_email: str = ""
):
    try:
        source = widget.source
        if is_report:
            widget = widget.report
        SourceQuery = get_source(slug=source)
        query_kwargs = {}
        if SourceQuery is None:
            raise Exception(
                f"could not find a source with the slug {source}, make sure that the widget is configured with a supported source"
            )

        default_filters, operation, op_field, limit = widget.source_config(
            sub_widget=filters.pop("slug", [None])[0]
        )

        default_filters.update(filters)

        project_timezone = widget.project.timezone
        apply_timezone_to_date_filters(default_filters, project_timezone)
        verify_filters(default_filters)

        if operation == "list":
            tags = default_filters.pop("tags", [None])[0]
            if tags:
                default_filters["tags"] = tags.split(",")

        if op_field:
            query_kwargs["field_name"] = op_field
        if limit:
            query_kwargs["limit"] = limit

        serialized_source = SourceQuery.execute(
            filters=default_filters,
            operation=operation,
            parser=parse_dict_to_json,
            project=widget.project,
            user_email=user_email,
            query_kwargs=query_kwargs,
        )
        return serialized_source
    except Widget.DoesNotExist:
        raise Exception("Widget not found.")
