from dataclasses import dataclass
from datetime import datetime

from ...domain.entities import Project
from ...domain.repositories import ProjectRepository


class CreateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    def execute(self, project=Project) -> Project:
        return self.project_repo.create(project)


@dataclass
class UpdateProjectInput:
    name: str
    timezone: str
    config: dict

    def __post_init__(self):
        self.updated_at = datetime.now()


class UpdateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    def execute(self, uuid: str, fields: UpdateProjectInput) -> Project:
        return self.project_repo.update(uuid=uuid, fields=fields.__dict__)


class DeleteProjectUseCase:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    def execute(self, uuid: str) -> bool:
        return self.project_repo.delete(uuid=uuid)


class GetProjectUseCase:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self.project_repo = project_repo

    def execute(self, uuid: str) -> bool:
        return self.project_repo.get(uuid=uuid)
