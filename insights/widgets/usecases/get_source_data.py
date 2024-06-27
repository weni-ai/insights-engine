from datetime import datetime, time

import pytz
from django.utils.timezone import make_aware, now

from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source
from insights.widgets.models import Widget


def set_live_day(default_filters: dict):
    start_of_day = datetime.combine(datetime.now().date(), datetime.min.time())
    default_filters.setdefault("filter", {})["created_on__gte"] = start_of_day


def apply_timezone_to_date_filters(default_filters: dict, timezone: str):
    tz = pytz.timezone(timezone)
    date_suffixes = ["__gte", "__lte"]

    if default_filters.get("created_on__gte") == "now":
        set_live_day(default_filters)

    for key, value in default_filters.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                if subkey.endswith(tuple(date_suffixes)):
                    if isinstance(subvalue, str):
                        date_value = datetime.strptime(subvalue, "%Y-%m-%d")
                    elif isinstance(subvalue, datetime):
                        date_value = subvalue

                    default_filters[key][subkey] = tz.localize(date_value)


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
