from django_app.projects.models import Project
from django_app.projects.project_dto import ProjectCreationDTO


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
        )

        return project
