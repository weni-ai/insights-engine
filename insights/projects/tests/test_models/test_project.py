import pytest

from insights.projects.models import Project


@pytest.mark.django_db
def test_create_project():
    project_name = "Test Project"
    project = Project.objects.create(name=project_name)

    assert Project.objects.count() == 1
    assert project.name == project_name


@pytest.mark.django_db
def test_live_desk_copilot_defaults():
    project = Project.objects.create(name="Test Project")

    assert project.is_live_desk_copilot is False
    assert project.uuid_live_desk_project is None
