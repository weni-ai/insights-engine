from datetime import datetime

import pytz

from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source
from insights.widgets.models import Widget


def apply_timezone_to_filters(default_filters, project_timezone_str):
    project_timezone = pytz.timezone(project_timezone_str)
    for key in default_filters.keys():
        if key.endswith("__gte") or key.endswith("__lte"):
            date_str = default_filters[key][0]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_obj_with_tz = project_timezone.localize(date_obj)
            default_filters[key] = date_obj_with_tz.isoformat()


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
        apply_timezone_to_filters(default_filters, project_timezone)

        if operation == "list":
            tags = default_filters.pop("tags", [None])[0]
            if tags:
                default_filters["tags"] = tags.split(",")

        if op_field:
            query_kwargs["op_field"] = op_field
        if limit:
            query_kwargs["limit"] = limit

        default_filters["project"] = str(widget.project.uuid)
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
