from insights.widgets.usecases.widget_dto import WidgetCreationDTO
from .project_dto import DashboardTemplateDTO

from django.db import transaction

from insights.dashboards.models import Dashboard

from .exceptions import InvalidDashboardTemplate

from insights.projects.usecases.dashboard_widgets import widgets_list
from insights.widgets.usecases.create_by_template import WidgetCreationUseCase


class DashboardUseCase:
    def create(self, project, dashboard_list):
        dashboard_to_create = []
        try:
            with transaction.atomic():
                for dashboard in dashboard_list:
                    dashboard = Dashboard(
                        project=project,
                        name=dashboard.name,
                        description=dashboard.description,
                        is_default="False",
                        from_template="True",
                        template=dashboard,
                    )
                    dashboard_to_create.append(dashboard)
                Dashboard.objects.bulk_create(dashboard_to_create)

                widget_dto_list = widgets_list(dashboard_to_create)

                widgets = WidgetCreationUseCase()
                widgets.create_widgets(widget_dtos=widget_dto_list)

        except Exception as exception:
            raise InvalidDashboardTemplate(f"Error creating dashboard: {exception}")
