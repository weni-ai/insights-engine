import pytest

from ..models import User


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(email="test@test.com")
    assert user.email == "test@test.com"
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_super_user():
    with pytest.raises(NotImplementedError):
        User.objects.create_superuser(email="test@test.com")


@pytest.mark.django_db
def test_create_user_without_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="")
