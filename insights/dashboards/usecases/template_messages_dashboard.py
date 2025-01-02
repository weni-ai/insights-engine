from typing import TYPE_CHECKING

from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
    InvalidWidgetsObject,
)
from insights.widgets.models import Widget


if TYPE_CHECKING:
    from insights.projects.models import Project


class CreateTemplateMessagesDashboard:
    def create_dashboard(self, project: "Project") -> None:
        try:
            with transaction.atomic():
                template_messages_dashboard = Dashboard.objects.create(
                    project=project,
                    name="Templates de mensagens",
                    description="Dashboard de templates de mensagens do WhatsApp Business",
                    is_default=False,
                    grid=[18, 4],
                    is_deletable=False,
                    is_editable=False,
                )
                self.create_widgets(template_messages_dashboard)
        except Exception as exp:
            raise InvalidDashboardObject(f"Error creating dashboard: {exp}")

    def create_widgets(self, dashboard: Dashboard) -> None:
        try:
            widgets_to_create = []
            widget_name_prefix = "template_messages_dashboard"

            widgets_to_create.append(
                Widget(
                    dashboard=dashboard,
                    name=f"{widget_name_prefix}.preview",
                    type="template_messages_preview_card",
                    source="template_messages",
                    config={
                        "operation": "retrieve_information",
                    },
                    position={"rows": [1, 4], "columns": [1, 3]},
                )
            )
            widgets_to_create.append(
                Widget(
                    dashboard=dashboard,
                    name=f"{widget_name_prefix}.messages_status_metrics",
                    type="count_metrics_with_graph_column",
                    source="template_messages",
                    config={
                        "operation": "timeseries_hour_group_count",
                    },
                    position={"rows": [1, 2], "columns": [4, 18]},
                )
            )
            widgets_to_create.append(
                Widget(
                    dashboard=dashboard,
                    name=f"{widget_name_prefix}.active_contacts_count",
                    type="card",
                    source="template_messages",
                    config={
                        "operation": "count",
                    },
                    position={"rows": [3, 3], "columns": [4, 11]},
                )
            )
            widgets_to_create.append(
                Widget(
                    dashboard=dashboard,
                    name=f"{widget_name_prefix}.blocks_count",
                    type="card",
                    source="template_messages",
                    config={
                        "operation": "count",
                    },
                    position={"rows": [3, 3], "columns": [11, 18]},
                )
            )
            widgets_to_create.append(
                Widget(
                    dashboard=dashboard,
                    name=f"{widget_name_prefix}.button_clicks",
                    type="table_dynamic_by_filter",
                    source="template_messages",
                    config={},  # TODO
                    position={"rows": [3, 3], "columns": [11, 18]},
                )
            )

        except Exception as exp:
            raise InvalidWidgetsObject(f"Error creating widgets: {exp}")
