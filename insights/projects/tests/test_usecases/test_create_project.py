from uuid import uuid4

import pytest

from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO


@pytest.mark.django_db
def test_create_project():
    project_dto = ProjectCreationDTO(
        uuid=uuid4().hex,
        name="test_name",
        is_template=False,
    )
    project = ProjectsUseCase().create_project(project_dto=project_dto)
    assert project.uuid == project_dto.uuid
