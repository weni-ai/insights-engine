from dataclasses import dataclass

from django.contrib.auth import get_user_model

from insights.projects.models import Project, ProjectAuth
from insights.projects.usecases import InvalidProjectAuth

User = get_user_model()


@dataclass
class ProjectAuthDTO:
    project: str
    user: str
    role: str


class ProjectAuthCreationUseCase:
    def role_mapping(self, role: int):
        # theres only two role atm, 0 and 1
        return int(role > 0)

    def get_project(self, project: str):
        # use project use case for retrieving by UUID
        return Project.objects.get(uuid=project)

    def get_or_create_user_by_email(self, email: str) -> tuple:
        return User.objects.get_or_create(email=email)

    def create_permission(self, project_permission_dto: ProjectAuthDTO):
        user, _ = self.get_or_create_user_by_email(project_permission_dto.user)
        role_value = self.role_mapping(int(project_permission_dto.role))
        project = self.get_project(project_permission_dto.project)

        project_permission = ProjectAuth.objects.update_or_create(
            project=project, user=user, defaults={"role": role_value}
        )[0]

        return project_permission

    def bulk_create(self, project: str, authorizations: list[dict]):
        if authorizations == []:
            return
        auth_instances = []
        project = self.get_project(project)
        for auth in authorizations:
            user = self.get_or_create_user_by_email(auth.get("user"))[0]
            instance = ProjectAuth(project=project, user=user, role=auth.get("role"))
            auth_instances.append(instance)
        ProjectAuth.objects.bulk_create(auth_instances, ignore_conflicts=True)

    def update_permission(self, project_permission_dto: ProjectAuthDTO):
        return self.create_permission(project_permission_dto)

    def delete_permission(self, project_permission_dto: ProjectAuthDTO):
        try:
            project_permission = ProjectAuth.objects.get(
                project=project_permission_dto.project,
                user=project_permission_dto.user,
            )
        except Exception as err:
            raise InvalidProjectAuth(err)

        project_permission.delete()
