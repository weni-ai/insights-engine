import functools

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from insights.projects.models import ProjectAuth

User = get_user_model()


def with_project_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        project = self.project
        user = self.user

        ProjectAuth.objects.create(project=project, user=user, role=1)

        return func(self, *args, **kwargs)

    return wrapper


def with_internal_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(User)
        user = self.user
        permission, _ = Permission.objects.get_or_create(
            codename="can_communicate_internally",
            content_type=content_type,
        )
        user.user_permissions.add(permission)

        return func(self, *args, **kwargs)

    return wrapper
