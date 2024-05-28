import pytest

from insights.projects.models import Project


@pytest.mark.django_db
def test_create_project():
    project_name = "Test Project"
    project = Project.objects.create(name=project_name)

    assert Project.objects.count() == 1
    assert project.name == project_name


@pytest.mark.django_db
def test_project_str_function():
    project_name = "Test Project"
    project = Project.objects.create(name=project_name)

    assert str(project) == f"{project.uuid} - Project: {project.name}"


@pytest.mark.django_db
def test_project_auth_str_function(create_project_auth):
    project_auth = create_project_auth

    assert (
        str(project_auth)
        == f"[{project_auth.role}] {project_auth.project.name} - {project_auth.user.email}"
    )
