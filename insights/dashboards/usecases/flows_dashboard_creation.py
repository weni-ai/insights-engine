from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
    InvalidWidgetsObject,
)
from insights.widgets.models import Widget


class CreateFlowsDashboard:
    def __init__(self, request):
        self.request = request
        self.funnel_amount = self.request.data.get("funnel_amount")
        self.dashboard_name = self.request.data.get("dashboard_name")

    def create_dashboard(self, project):
        try:
            with transaction.atomic():
                dashboard_resultado_de_fluxo = Dashboard.objects.create(
                    project=project,
                    name=self.dashboard_name,
                    description="Dashboard de resultado de fluxo personalizado",
                    is_default=False,
                    grid=[12, 3],
                    is_deletable=True,
                    is_editable=True,
                )
                self.create_widgets(dashboard_resultado_de_fluxo)

        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")

    def create_widgets(self, dashboard_resultado_de_fluxo):
        if self.funnel_amount == 3:
            try:
                with transaction.atomic():
                    for _ in range(3):
                        Widget.objects.create(
                            name="Funil",
                            type="graph_funnel",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position={"rows": [1, 3], "columns": [9, 12]},
                        )
            except Exception as exception:
                raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

        elif self.funnel_amount == 2:
            try:
                with transaction.atomic():
                    for _ in range(2):
                        Widget.objects.create(
                            name="Funil",
                            type="graph_funnel",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position={"rows": [1, 3], "columns": [9, 12]},
                        )
                    for _ in range(3):
                        Widget.objects.create(
                            name="",
                            type="card",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position={"rows": [3, 3], "columns": [5, 8]},
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
                    for _ in range(6):
                        Widget.objects.create(
                            name="",
                            type="card",
                            source="",
                            config={},
                            dashboard=dashboard_resultado_de_fluxo,
                            position={"rows": [3, 3], "columns": [5, 8]},
                        )
            except Exception as exception:
                raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

        try:
            with transaction.atomic():
                for _ in range(9):
                    Widget.objects.create(
                        name="",
                        type="card",
                        source="",
                        config={},
                        dashboard=dashboard_resultado_de_fluxo,
                        position={"rows": [3, 3], "columns": [5, 8]},
                    )
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")
