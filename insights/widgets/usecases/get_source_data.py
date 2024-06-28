from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source
from insights.widgets.models import Widget


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
        )  # implement a dynamic handler for each widget

        filters.update(default_filters)
        if operation == "list":
            tags = filters.pop("tags", [None])[0]
            if tags:
                filters["tags"] = tags.split(",")

        if op_field:
            query_kwargs["op_field"] = op_field
        if limit:
            query_kwargs["limit"] = limit

        serialized_source = SourceQuery.execute(
            filters=filters,
            operation=operation,
            parser=parse_dict_to_json,
            project=widget.project,
            user_email=user_email,
            query_kwargs=query_kwargs,
        )
        return serialized_source
    except Widget.DoesNotExist:
        raise Exception("Widget not found.")
