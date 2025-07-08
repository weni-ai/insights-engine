from insights.dashboards.usecases.conversations_dashboard_creation import (
    ConversationsDashboardCreation,
)
from insights.projects.models import Project

from .project_dto import ProjectCreationDTO

from insights.dashboards.usecases.human_service_dashboard_creation import (
    CreateHumanService,
)


class ProjectsUseCase:

    def get_by_uuid(self, project_uuid: str) -> Project:
        try:
            return Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            raise Exception(
                f"[ ProjectsUseCase ] Project with uuid `{project_uuid}` does not exists!"
            )
        except Exception as exception:
            raise Exception(f"[ ProjectsUseCase ] error: {str(exception)}")

    def create_project(self, project_dto: ProjectCreationDTO) -> Project:
        project = Project.objects.create(
            uuid=project_dto.uuid,
            name=project_dto.name,
            is_template=project_dto.is_template,
            timezone=project_dto.timezone,
            date_format=project_dto.date_format,
            vtex_account=project_dto.vtex_account,
        )
        CreateHumanService().create_dashboard(project)
        ConversationsDashboardCreation().create_for_project(project)
        return project
