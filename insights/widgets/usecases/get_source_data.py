from datetime import datetime

import pytz
from django.utils import timezone

from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source
from insights.widgets.models import Widget


def set_live_day(default_filters):
    start_of_day = datetime.combine(timezone.now().date(), datetime.min.time())

    for key, value in default_filters.items():
        if value == "today":
            default_filters[key] = start_of_day


def apply_timezone_to_filters(default_filters, project_timezone_str):
    project_timezone = pytz.timezone(project_timezone_str)
    for key in default_filters.keys():
        if key.endswith("__gte") or key.endswith("__lte"):
            value = default_filters[key]
            if isinstance(value, list):
                date_str = value[0]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            elif isinstance(value, datetime):
                date_obj = value
            else:
                raise ValueError(
                    f"Unexpected value type for filter {key}: {type(value)}"
                )

            date_obj_with_tz = project_timezone.localize(date_obj)
            default_filters[key] = date_obj_with_tz.isoformat()


class Calculator:
    def __init__(self, operand_1, operand_2, operator) -> None:
        self.operand_1 = operand_1
        self.operand_2 = operand_2
        self.operator = operator

    def sum(self):
        return self.operand_1 + self.operand_2

    def sub(self):
        return self.operand_1 - self.operand_2

    def multiply(self):
        return self.operand_1 * self.operand_2

    def percentage(self):
        return 100 * (self.operand_2 / self.operand_1)

    def evaluate(self):
        return getattr(self, self.operator)()


def simple_source_data_operation(
    source_query,
    widget: Widget,
    is_live: bool = False,
    filters: dict = {},
    user_email: str = "",
    auth_params: dict = {},
):
    query_kwargs = {}

    sub = filters.pop("slug", [None])
    if sub in ["subwidget_1", "subwidget_2"]:
        default_filters, operation, op_field, op_sub_field, limit = (
            widget.source_config(sub_widget=sub, is_live=is_live)
        )
    else:
        default_filters, operation, op_field, op_sub_field, limit = (
            widget.source_config(sub_widget=sub[0], is_live=is_live)
        )

    default_filters.update(filters)

    if is_live:
        set_live_day(default_filters)

    project_timezone = widget.project.timezone
    apply_timezone_to_filters(default_filters, project_timezone)

    if operation == "list":
        tags = default_filters.pop("tags", [None])[0]
        if tags:
            default_filters["tags"] = tags.split(",")

    if op_field:
        query_kwargs["op_field"] = op_field
    if op_sub_field:
        query_kwargs["op_sub_field"] = op_sub_field
    if limit:
        query_kwargs["limit"] = limit
    if project_timezone:
        query_kwargs["timezone"] = project_timezone

    default_filters["project"] = str(widget.project.uuid)
    serialized_source = source_query.execute(
        filters=default_filters,
        operation=operation,
        parser=parse_dict_to_json,
        project=widget.project,
        user_email=user_email,
        query_kwargs=query_kwargs,
        auth_params=auth_params,
    )
    return serialized_source


def cross_source_data_operation(
    source_query,
    widget: Widget,
    is_live: bool = False,
    filters: dict = {},
    user_email: str = "",
    calculator=Calculator,
    auth_params: dict = {},
):
    """
    there will always be two subwidgets to make a cross operation,
    until the business rule is updated.
    so we save then in fixed positions(subwidget slug) on the config dict
    """
    # The subwidget needs to have a operation that returns a value(count, sum, avg...), cannot be a list of values
    filters["slug"] = "subwidget_1"
    subwidget_1_data = simple_source_data_operation(
        source_query, widget, is_live, filters, user_email, auth_params
    )[
        "value"
    ]  # TODO: Treat other ways(test to see if there are) to get the value(other names for the value field)
    filters["slug"] = "subwidget_2"
    subwidget_2_data = simple_source_data_operation(
        source_query, widget, is_live, filters, user_email, auth_params
    )[
        "value"
    ]  # TODO: Treat other ways(test to see if there are) to get the value(other names for the value field)
    operator = widget.config.get("operator")

    result = calculator(subwidget_1_data, subwidget_2_data, operator).evaluate()
    return {"value": result}


def get_source_data_from_widget(
    widget: Widget,
    is_report: bool = False,
    is_live=False,
    filters: dict = {},
    user_email: str = "",
):
    try:
        source = widget.source
        if is_report:
            widget = widget.report
        SourceQuery = get_source(slug=source)
        if SourceQuery is None:
            raise Exception(
                f"could not find a source with the slug {source}, make sure that the widget is configured with a supported source"
            )

        serialized_auth = {}
        if widget.type == "vtex_order":
            auth_source = get_source(slug="vtexcredentials")
            serialized_auth: dict = auth_source.execute(
                filters={"project": widget.project.uuid},
                operation="get_vtex_auth",
                parser=parse_dict_to_json,
                return_format="",
                query_kwargs={},
            )

        operation_function = (
            cross_source_data_operation
            if widget.is_crossing_data
            else simple_source_data_operation
        )

        return operation_function(
            widget=widget,
            source_query=SourceQuery,
            is_live=is_live,
            filters=filters,
            user_email=user_email,
            auth_params=serialized_auth,
        )

    except Widget.DoesNotExist:
        raise Exception("Widget not found.")

    except KeyError:
        raise Exception(
            "The subwidgets operation needs to be one that returns only one object value."
        )
