from pytest import fixture

from insights.dashboards.models import Dashboard
from insights.projects.models import Project
from insights.users.models import User


@fixture
def create_user():
    return User.objects.create_user("test@user.com")


@fixture
def create_project():
    return Project.objects.create(name="Test Project")


@fixture
def create_default_dashboard(create_project):
    return Dashboard.objects.create(
        project=create_project,
        name="Human Resources",
        description="Dashboard populated with HR data, for HR managers",
        is_default=True,
    )


@fixture
def create_not_default_dashboard(create_project):
    return Dashboard.objects.create(
        project=create_project,
        name="Human Resources",
        description="Dashboard populated with HR data, for HR managers",
        is_default=False,
    )
