import functools

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from weni_commons.auth import TOKEN_TYPE_KEYCLOAK, WeniAuthContext

from insights.projects.models import ProjectAuth

User = get_user_model()


def build_keycloak_auth_context(
    user,
    *,
    project=None,
    project_uuid=None,
    vtex_account=None,
    is_internal: bool = False,
) -> WeniAuthContext:
    """Build a Keycloak-style ``WeniAuthContext`` for ``force_authenticate``."""
    resolved_project_uuid = project_uuid
    if resolved_project_uuid is None and project is not None:
        resolved_project_uuid = str(project.uuid)

    return WeniAuthContext(
        project_uuid=str(resolved_project_uuid) if resolved_project_uuid else None,
        vtex_account=vtex_account,
        user_email=getattr(user, "email", None),
        is_internal=is_internal,
        token_type=TOKEN_TYPE_KEYCLOAK,
    )


def with_project_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        project = self.project
        user = self.user

        ProjectAuth.objects.create(project=project, user=user, role=1)
        self.client.force_authenticate(
            user=user,
            token=build_keycloak_auth_context(user, project=project),
        )

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

        project = getattr(self, "project", None)
        self.client.force_authenticate(
            user=user,
            token=build_keycloak_auth_context(
                user, project=project, is_internal=True
            ),
        )

        return func(self, *args, **kwargs)

    return wrapper
