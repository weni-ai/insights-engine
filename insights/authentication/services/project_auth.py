import logging

import requests
from django.conf import settings
from rest_framework.permissions import SAFE_METHODS

from insights.authentication.services.exceptions import ProjectAuthorizationDenied
from insights.projects.models import ProjectAuth

logger = logging.getLogger(__name__)

EXISTING_ROLES = {
    "not_set": 0,
    "viewer": 1,
    "contributor": 2,
    "moderator": 3,
    "support": 4,
    "chat_user": 5,
}


def _check_project_authorization(
    token: str, project_uuid: str, method: str
) -> tuple[bool, str | None]:
    base_url = settings.PROJECT_AUTH_API_BASE_URL
    url = f"{base_url}/v2/projects/{project_uuid}/authorization"

    response = requests.get(
        url,
        headers={"Authorization": token},
        timeout=settings.PROJECT_AUTH_API_TIMEOUT,
    )

    if response.status_code != 200:
        raise ProjectAuth.DoesNotExist(
            "You do not have permission to perform this action."
        )

    data = response.json()
    user_email = data.get("user")
    role = data.get("project_authorization")

    if role == EXISTING_ROLES["viewer"] and method.upper() in SAFE_METHODS:
        return True, user_email

    raise ProjectAuthorizationDenied(
        "You do not have permission to perform this action."
    )


def has_external_general_project_permission(request, project_uuid) -> bool:
    project_uuid = str(project_uuid)
    cache = getattr(request, "_external_project_auth_cache", None)
    if cache is None:
        cache = {}
        request._external_project_auth_cache = cache

    if project_uuid in cache:
        return cache[project_uuid]

    token = request.headers.get("Authorization")
    if not token:
        cache[project_uuid] = False
        return False

    try:
        authorized, user_email = _check_project_authorization(
            token, project_uuid, request.method
        )
    except ProjectAuthorizationDenied:
        cache[project_uuid] = False
        return False
    except (requests.RequestException, ProjectAuth.DoesNotExist) as exc:
        logger.warning(
            "External project auth check failed for project=%s: %s",
            project_uuid,
            exc,
        )
        cache[project_uuid] = False
        return False

    request_user_email = getattr(request.user, "email", None)
    if user_email and request_user_email and user_email != request_user_email:
        logger.warning(
            "External project auth user mismatch for project=%s "
            "(token user=%s, request user=%s)",
            project_uuid,
            user_email,
            request_user_email,
        )
        cache[project_uuid] = False
        return False

    if user_email:
        request.project_auth_user_email = user_email

    cache[project_uuid] = authorized
    return authorized
