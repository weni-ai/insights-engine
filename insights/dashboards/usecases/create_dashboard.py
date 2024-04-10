from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.projects.usecases.create import ProjectsUseCase

from .dashboard_dto import DashboardCreationDTO


class DashboardCreateUseCase:
    def __init__(
        self,
        project_usecase=ProjectsUseCase,
    ) -> None:
        self.project_usecase = project_usecase

    def remove_old_is_default(self, project):
        Dashboard.objects.filter(is_default=True, project=project).update(
            is_default=False
        )

    @transaction.atomic
    def execute(self, dash_dto: DashboardCreationDTO):
        project = self.project_usecase().get_by_uuid(dash_dto.project)

        if dash_dto.is_default is True:
            self.remove_old_is_default(project)

        return Dashboard.objects.create(
            project=project,
            name=dash_dto.name,
            description=dash_dto.description,
            is_default=dash_dto.is_default,
            from_template=dash_dto.from_template,
            template=dash_dto.template,
        )
