import pytest

from insights.users.usecases import UserDoesNotExists, get_by_email

from .user_factory import UserFactory


@pytest.mark.django_db
def test_get_by_email():
    user = UserFactory()
    retrieved_user = get_by_email(user.email)
    assert user == retrieved_user


@pytest.mark.django_db
def test_get_by_email_nonexistent():
    with pytest.raises(UserDoesNotExists):
        get_by_email("nonexistent_email")


@pytest.mark.django_db
def test_get_by_email_invalid():
    with pytest.raises(UserDoesNotExists):
        get_by_email("invalid_email")


@pytest.mark.django_db
def test_get_by_email_none():
    with pytest.raises(UserDoesNotExists):
        get_by_email(None)
