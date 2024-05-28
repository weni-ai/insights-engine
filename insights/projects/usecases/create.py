from insights.projects.models import Project

from .project_dto import ProjectCreationDTO

from .create_dashboard_template import DashboardUseCase

from insights.dashboards.models import DashboardTemplate


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

        dashboard_list = list(
            DashboardTemplate.objects.filter(
                name__in=["atendimento humano", "jornada do bot"]
            )
        )

        dashboard_creation = DashboardUseCase()
        dashboard_creation.create(project, dashboard_list)
        return project
