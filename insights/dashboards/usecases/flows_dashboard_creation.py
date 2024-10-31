from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
    InvalidWidgetsObject,
)
from insights.widgets.models import Widget
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO


class CreateFlowsDashboard:
    def __init__(self, params: FlowsDashboardCreationDTO):
        self.project = params.project
        self.dashboard_name = params.dashboard_name
        self.funnel_amount = params.funnel_amount
        self.currency_type = params.currency_type

    def create_dashboard(self):
        try:
            with transaction.atomic():
                dashboard_resultado_de_fluxo = Dashboard.objects.create(
                    project=self.project,
                    name=self.dashboard_name,
                    description="Dashboard de resultado de fluxo personalizado",
                    is_default=False,
                    grid=[12, 3],
                    is_deletable=True,
                    is_editable=True,
                    config={"currency_type": self.currency_type},
                )
                self.create_widgets(dashboard_resultado_de_fluxo)
            return dashboard_resultado_de_fluxo
        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")

    def create_widgets(self, dashboard_resultado_de_fluxo):
        try:
            with transaction.atomic():
                if self.funnel_amount == 3:
                    self.create_graph_funnel_widgets(dashboard_resultado_de_fluxo, 3)
                elif self.funnel_amount == 2:
                    self.create_graph_funnel_widgets(dashboard_resultado_de_fluxo, 2)
                    self.create_card_widgets(dashboard_resultado_de_fluxo, 3)
                elif self.funnel_amount == 1:
                    self.create_graph_funnel_widgets(dashboard_resultado_de_fluxo, 1)
                    self.create_card_widgets(dashboard_resultado_de_fluxo, 6)
                else:
                    self.create_default_card_widgets(dashboard_resultado_de_fluxo)
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

    def create_graph_funnel_widgets(self, dashboard, amount):
        positions = {
            3: [
                {"rows": [1, 3], "columns": [1, 4]},
                {"rows": [1, 3], "columns": [5, 8]},
                {"rows": [1, 3], "columns": [9, 12]},
            ],
            2: [
                {"rows": [1, 3], "columns": [5, 8]},
                {"rows": [1, 3], "columns": [9, 12]},
            ],
            1: [
                {"rows": [1, 3], "columns": [9, 12]},
            ],
        }

        for position in positions[amount]:
            Widget.objects.create(
                name="Funil",
                type="empty_column",
                source="",
                config={},
                dashboard=dashboard,
                position=position,
            )

    def create_card_widgets(self, dashboard, amount):
        col_ranges = [[1, 4], [5, 8]]
        for i in range(amount):
            group = i // 3
            row = [(i % 3) + 1, (i % 3) + 1]
            col = col_ranges[group % 2]
            Widget.objects.create(
                name="",
                type="card",
                source="",
                config={},
                dashboard=dashboard,
                position={"rows": row, "columns": col},
            )

    def create_default_card_widgets(self, dashboard):
        col_ranges = [[1, 4], [5, 8], [9, 12]]

        for i in range(9):
            group = i // 3
            row = [(i % 3) + 1, (i % 3) + 1]
            col = col_ranges[group]

            Widget.objects.create(
                name="",
                type="card",
                source="",
                config={},
                dashboard=dashboard,
                position={"rows": row, "columns": col},
            )
