import pytest

from insights.projects.usecases import InvalidProjectAuth
from insights.projects.usecases.auth_creation import (
    ProjectAuthCreationUseCase,
    ProjectAuthDTO,
)


@pytest.mark.django_db
def test_create_or_update_admin_auth(create_project, create_user):
    proj = create_project
    user = create_user
    role = 1

    auth = ProjectAuthCreationUseCase().create_permission(
        ProjectAuthDTO(project=str(proj.uuid), user=user.email, role=role)
    )
    assert auth.project == proj
    assert auth.user == user
    assert auth.role == role


@pytest.mark.django_db
def test_bulk_create_admin_auth(create_project):
    proj = create_project
    assert proj.authorizations.count() == 0
    ProjectAuthCreationUseCase().bulk_create(
        project=str(proj.uuid),
        authorizations=[
            {"user": "john.doe@weni.ai", "role": 1},
            {"user": "lina.lawson@weni.ai", "role": 1},
            {"user": "agent@weni.ai", "role": 0},
        ],
    )
    assert proj.authorizations.count() == 3


@pytest.mark.django_db
def test_bulk_create_admin_auth_with_conflict(create_project_auth):
    proj = create_project_auth.project
    assert proj.authorizations.count() == 1
    ProjectAuthCreationUseCase().bulk_create(
        project=str(proj.uuid),
        authorizations=[
            {"user": create_project_auth.user.email, "role": 1},
            {"user": "lina.lawson@weni.ai", "role": 1},
            {"user": "agent@weni.ai", "role": 0},
        ],
    )
    assert proj.authorizations.count() == 3


@pytest.mark.django_db
def test_bulk_create_admin_auth_with_empty_list(create_project):
    proj = create_project
    ProjectAuthCreationUseCase().bulk_create(
        project=str(proj.uuid),
        authorizations=[],
    )
    assert proj.authorizations.count() == 0


@pytest.mark.parametrize(
    "method",
    [
        "create",
        "update",
    ],
)
@pytest.mark.django_db
def test_update_auth(method, create_project_auth):
    auth = create_project_auth
    role = 0
    usecase = ProjectAuthCreationUseCase()
    write_method = getattr(usecase, f"{method}_permission")
    auth = write_method(
        ProjectAuthDTO(project=str(auth.project.uuid), user=auth.user.email, role=role)
    )
    assert auth.role == role


@pytest.mark.parametrize(
    "method",
    [
        "create",
        "update",
    ],
)
@pytest.mark.django_db
def test_create_or_update_auth_create_user(method, create_project):
    project = create_project
    user = "user@inexistent.com"
    role = 1
    usecase = ProjectAuthCreationUseCase()
    write_method = getattr(usecase, f"{method}_permission")
    auth = write_method(ProjectAuthDTO(project=str(project.uuid), user=user, role=role))
    assert auth.project == project
    assert auth.user.email == user
    assert auth.role == role


@pytest.mark.django_db
def test_delete_auth(create_project_auth):
    auth = create_project_auth
    proj = auth.project
    assert proj.authorizations.count() == 1
    assert (
        ProjectAuthCreationUseCase().delete_permission(
            ProjectAuthDTO(project=str(proj.uuid), user=auth.user.email, role=0)
        )
        is None
    )
    assert proj.authorizations.count() == 0


@pytest.mark.django_db
def test_delete_inexistent_user_auth(create_project):
    proj = create_project
    with pytest.raises(InvalidProjectAuth):
        ProjectAuthCreationUseCase().delete_permission(
            ProjectAuthDTO(project=str(proj.uuid), user="user@inexistent.com", role=0)
        )
