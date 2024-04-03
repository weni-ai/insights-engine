from uuid import uuid4

import pytest

from insights.projects.usecases.create import ProjectsUseCase

from .project_factory import ProjectFactory


@pytest.mark.django_db
def test_get_by_uuid():
    project = ProjectFactory()
    retrieved_project = ProjectsUseCase().get_by_uuid(project.uuid)
    assert project == retrieved_project


@pytest.mark.django_db
def test_non_existent_project():
    with pytest.raises(Exception):
        ProjectsUseCase().get_by_uuid(uuid4().hex)


@pytest.mark.django_db
def test_invalid_uuid():
    with pytest.raises(Exception):
        ProjectsUseCase().get_by_uuid("invalid_uuid")
