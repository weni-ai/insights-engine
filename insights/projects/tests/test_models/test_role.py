import pytest

from insights.projects.models import Roles


@pytest.mark.parametrize(
    "role,name",
    [
        (0, "NOT_SETTED"),
        (1, "ADMIN"),
    ],
)
def test_none_and_admin_roles(role, name):
    """
    Ensures that this roles are implemented in the correct order
    """
    assert getattr(Roles, name) == role


def test_get_non_existant_role():
    with pytest.raises(AttributeError):
        getattr(Roles, "ROLE_THAT_DOES_NOT_EXIST")
