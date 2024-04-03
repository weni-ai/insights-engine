from pytest import fixture

from insights.dashboards.models import Dashboard, DashboardTemplate
from insights.projects.models import Project, ProjectAuth
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


@fixture
def create_project_dashboard_template(create_project):
    project = create_project
    return DashboardTemplate.objects.create(
        project=project,
        name="Dashboard Template example",
        description="very good dashboard to analyze your project data",
        config={"example": "use only for testing the models"},
    )


@fixture
def create_project_auth(create_project, create_user):
    proj = create_project
    user = create_user
    role = 1

    return ProjectAuth.objects.create(project=proj, user=user, role=role)
