import pytest
from django.db.utils import IntegrityError

from insights.dashboards.models import Dashboard


@pytest.mark.django_db
def test_create_dashboard(create_project):
    name = "Human Resources"
    description = "Dashboard populated with HR data, for HR managers"

    project = create_project
    dashboard = Dashboard.objects.create(
        project=project,
        name=name,
        description=description,
        is_default=True,
    )
    assert project.dashboards.count() == 1
    assert dashboard.name == name
    assert dashboard.description == description


@pytest.mark.django_db
def test_create_dashboard_whithout_is_default(create_project):
    project = create_project
    dashboard = Dashboard.objects.create(
        project=project,
        name="Human Resources",
        description="Dashboard populated with HR data, for HR managers",
    )

    assert dashboard.is_default is False


@pytest.mark.django_db
def test_can_only_have_one_default_dashboard(create_project, create_default_dashboard):
    with pytest.raises(IntegrityError):
        Dashboard.objects.create(
            project=create_project,
            name="Human Resources",
            description="Dashboard populated with HR data, for HR managers",
            is_default=True,
        )
