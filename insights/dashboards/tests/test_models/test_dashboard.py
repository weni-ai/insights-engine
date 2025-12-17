import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from insights.dashboards.models import HUMAN_SERVICE_DASHBOARD_V1_NAME, Dashboard
from insights.projects.models import Project


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


class TestDashboardModel(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.human_service_dashboard = Dashboard.objects.create(
            project=self.project,
            name=HUMAN_SERVICE_DASHBOARD_V1_NAME,
            description="Example",
            is_default=False,
        )

    def test_delete_non_default_dashboard(self):
        self.assertFalse(self.human_service_dashboard.is_default)

        dashboard = Dashboard.objects.create(
            project=self.project,
            name="Example",
            description="Example",
            is_default=False,
        )
        dashboard_id = dashboard.uuid

        dashboard.delete()

        self.assertFalse(Dashboard.objects.filter(uuid=dashboard_id).exists())
        self.human_service_dashboard.refresh_from_db(fields=["is_default"])
        self.assertFalse(self.human_service_dashboard.is_default)

    def test_delete_default_dashboard(self):
        self.assertFalse(self.human_service_dashboard.is_default)

        dashboard = Dashboard.objects.create(
            project=self.project,
            name="Example",
            description="Example",
            is_default=True,
        )
        dashboard_id = dashboard.uuid

        dashboard.delete()

        self.assertFalse(Dashboard.objects.filter(uuid=dashboard_id).exists())
        self.human_service_dashboard.refresh_from_db(fields=["is_default"])
        self.assertTrue(self.human_service_dashboard.is_default)
