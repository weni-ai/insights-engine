from django_app.dashboards.models import Dashboard
from django_app.usecases import projects


class CreateDashboardUseCase:
    """
    verify if the project exists
    verify if the user have permission
    create dashboard model instance with the given data
    """

    def execute(
        self, project: str, description: str, template: str, user: str
    ) -> Dashboard: ...
