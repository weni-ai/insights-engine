import pytest

from insights.projects.models import ProjectAuth, Roles


@pytest.mark.django_db
def test_create_project_auth(create_user, create_project):
    auth = ProjectAuth.objects.create(
        user=create_user, project=create_project, role=Roles.ADMIN
    )
    assert auth.user == create_user
    assert auth.project == create_project
    assert auth.role == Roles.ADMIN
