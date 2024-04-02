import pytest

from insights.dashboards.models import DashboardTemplate


@pytest.mark.django_db
def test_create_dashboard():
    name = "Human Resources"
    description = "Dashboard populated with HR data, for HR managers"
    config = {
        "example": "the template config details are to be implemented in the use case layers"
    }

    dashboard_template = DashboardTemplate.objects.create(
        name=name, description=description, config=config
    )
    assert dashboard_template.name == name
    assert dashboard_template.description == description
    assert dashboard_template.config == config


@pytest.mark.django_db
def test_create_dashboard_template_with_project(create_project):
    name = "Human Resources"
    description = "Dashboard populated with HR data, for HR managers"
    project = create_project
    config = {
        "example": "the template config details are to be implemented in the use case layers"
    }

    dashboard_template = DashboardTemplate.objects.create(
        project=project,
        name=name,
        description=description,
        config=config,
    )

    assert dashboard_template.name == name
    assert dashboard_template.description == description
    assert project.dashboard_templates.count() == 1


@pytest.mark.django_db
def test_create_dashboard_template_with_deleted_project(
    create_project_dashboard_template,
):
    dashboard_template = create_project_dashboard_template
    project = dashboard_template.project
    project.delete()

    dashboard_template.refresh_from_db()

    assert dashboard_template.project is None
