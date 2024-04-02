from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"

    email = models.EmailField("email", unique=True)
    language = models.CharField(
        max_length=64,
        choices=settings.LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
    )
    is_active = models.BooleanField(default=True)

    objects = UserManager()
