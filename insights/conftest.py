from pytest import fixture

from insights.projects.models import Project
from insights.users.models import User


@fixture
def create_user():
    return User.objects.create_user("test@user.com")


@fixture
def create_project():
    return Project.objects.create(name="Test Project")
