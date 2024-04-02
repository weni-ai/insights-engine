import pytest

from insights.projects.models import Project


@pytest.mark.django_db
def test_create_project():
    project_name = "Test Project"
    project = Project.objects.create(name=project_name)

    assert Project.objects.count() == 1
    assert project.name == project_name
