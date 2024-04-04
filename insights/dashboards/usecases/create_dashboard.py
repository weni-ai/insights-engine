from insights.dashboards.models import Dashboard
from insights.projects.usecases.create import ProjectsUseCase

from .dashboard_dto import DashboardCreationDTO


class DashboardCreateUseCase:
    def __init__(
        self, project_usecase=ProjectsUseCase, storage_manager=Dashboard.objects
    ) -> None:
        self.project_usecase = project_usecase
        self.storage_manager = storage_manager

    def execute(self, dash_dto: DashboardCreationDTO):
        project = self.project_usecase().get_by_uuid(dash_dto.project)
        return self.storage_manager.create(
            project=project,
            name=dash_dto.name,
            description=dash_dto.description,
            is_default=dash_dto.is_default,
            from_template=dash_dto.from_template,
            template=dash_dto.template,
        )
