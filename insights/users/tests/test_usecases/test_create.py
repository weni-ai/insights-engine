import pytest

from insights.users.models import User
from insights.users.usecases import CreateUserUseCase


@pytest.mark.django_db
def test_create_by_email():
    user = CreateUserUseCase().create_user("test@create.com")
    assert user.email, "test@create.com"
    assert isinstance(user, User)
