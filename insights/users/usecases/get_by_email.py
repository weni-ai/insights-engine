from django.core.exceptions import ValidationError

from insights.users.models import User

from .exceptions import UserDoesNotExists


def get_by_email(user_email: str) -> User:
    try:
        return User.objects.get(email=user_email)
    except (User.DoesNotExist, ValidationError):
        raise UserDoesNotExists(f"User `{user_email}` does not exists!")
