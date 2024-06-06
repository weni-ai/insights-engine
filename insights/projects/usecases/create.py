from insights.projects.models import Project

from .project_dto import ProjectCreationDTO

from insights.dashboards.usecases.dashboard_creation import (
    create_atendimento_humano,
    create_resultado_de_fluxo,
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
        )
        create_atendimento_humano.create_dashboard(project)
        create_resultado_de_fluxo.create_dashboard(project)
        return project
