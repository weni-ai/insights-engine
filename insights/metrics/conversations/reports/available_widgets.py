from uuid import UUID
from insights.widgets.models import Widget
from insights.projects.models import Project


def get_csat_ai_widget(project: Project) -> Widget | None:
    widget = Widget.objects.filter(
        dashboard__project=project,
        source="conversations.csat",
        config__datalake_config__type__iexact="CSAT",
    ).first()

    if not widget or not widget.get_config("datalake_config", {}).get("agent_uuid"):
        return None

    return widget


def get_nps_ai_widget(project: Project) -> Widget | None:
    widget = Widget.objects.filter(
        dashboard__project=project,
        source="conversations.nps",
        config__datalake_config__type__iexact="NPS",
    ).first()

    if not widget or not widget.get_config("datalake_config", {}).get("agent_uuid"):
        return None

    return widget


def get_csat_human_widget(project: Project) -> Widget | None:
    widget = Widget.objects.filter(
        dashboard__project=project,
        source="conversations.csat",
        config__type="flow_result",
    ).first()

    if not widget:
        return None

    if not widget.get_config("filter", {}).get("flow") or not widget.get_config(
        "op_field"
    ):
        return None

    return widget


def get_nps_human_widget(project: Project) -> Widget | None:
    widget = Widget.objects.filter(
        dashboard__project=project,
        source="conversations.nps",
        config__type="flow_result",
    ).first()

    if not widget:
        return None

    if not widget.get_config("filter", {}).get("flow") or not widget.get_config(
        "op_field"
    ):
        return None

    return widget


def get_custom_widgets(project: Project) -> list[UUID]:
    return Widget.objects.filter(
        dashboard__project=project,
        source="conversations.custom",
    ).values_list("uuid", flat=True)
