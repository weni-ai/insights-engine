from pytest import fixture
from insights.dashboards.models import (
    Dashboard,
    DashboardTemplate,
)  # Inclua Widget aqui
from insights.projects.models import Project, ProjectAuth
from insights.users.models import User
from insights.widgets.models import Widget


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
def create_editable_dashboard(create_project):
    return Dashboard.objects.create(
        project=create_project,
        name="Human Resources",
        description="Dashboard populated with HR data, for HR managers",
        is_default=False,
        is_editable=True,
    )


@fixture
def create_no_editable_dashboard(create_project):
    return Dashboard.objects.create(
        project=create_project,
        name="Human Resources",
        description="Dashboard populated with HR data, for HR managers",
        is_default=False,
        is_editable=False,
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


# Adicionar fixture para criar Widgets com o campo `source`
@fixture
def create_widget(create_default_dashboard):
    return Widget.objects.create(
        dashboard=create_default_dashboard,
        name="Example Widget",
        source="flows",  # Preencha o campo source com um valor válido
        config={"example": "widget config"},
    )
