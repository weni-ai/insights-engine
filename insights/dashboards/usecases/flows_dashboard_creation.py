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
        if self.funnel_amount == 3:
            try:
                with transaction.atomic():
                    positions = [
                        {"rows": [1, 3], "columns": [1, 4]},
                        {"rows": [1, 3], "columns": [5, 8]},
                        {"rows": [1, 3], "columns": [9, 12]},
                    ]

                    for position in positions:
                        Widget.objects.create(
                            name="Funil",
                            type="graph_funnel",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position=position,
                        )
            except Exception as exception:
                raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

        elif self.funnel_amount == 2:
            try:
                with transaction.atomic():
                    positions = [
                        {"rows": [1, 3], "columns": [5, 8]},
                        {"rows": [1, 3], "columns": [9, 12]},
                    ]
                    for funnel_positions in positions:
                        Widget.objects.create(
                            name="Funil",
                            type="graph_funnel",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position=funnel_positions,
                        )

                        col_ranges = [[1, 4]]
                        for i in range(3):
                            row = [(i % 3) + 1, (i % 3) + 1]
                            col = col_ranges[0]

                            Widget.objects.create(
                                name="",
                                type="card",
                                source="",
                                config={},
                                dashboard=dashboard_resultado_de_fluxo,
                                position={"rows": row, "columns": col},
                            )
            except Exception as exception:
                raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

        elif self.funnel_amount == 1:
            try:
                with transaction.atomic():
                    Widget.objects.create(
                        name="Funil",
                        type="graph_funnel",
                        source="",
                        config={},
                        dashboard=dashboard_resultado_de_fluxo,
                        position={"rows": [1, 3], "columns": [9, 12]},
                    )
                    col_ranges = [[1, 4], [5, 8]]

                    for i in range(6):
                        group = i // 3
                        row = [(i % 3) + 1, (i % 3) + 1]
                        col = col_ranges[group]
                        Widget.objects.create(
                            name="",
                            type="card",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position={"rows": row, "columns": col},
                        )
            except Exception as exception:
                raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

        try:
            with transaction.atomic():
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
                        dashboard=dashboard_resultado_de_fluxo,
                        position={"rows": row, "columns": col},
                    )
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")
