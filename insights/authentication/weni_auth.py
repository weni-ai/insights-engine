"""Helpers for WeniAuthentication / WeniAuthViewMixin consumers."""

from typing import Mapping, MutableMapping, Sequence

from rest_framework.request import Request
from weni_commons.auth import WeniAuthentication, get_auth_context


def weni_authentication_classes(
    base_classes: Sequence | None = None,
) -> list:
    """
    Prepend ``WeniAuthentication`` so JWT is tried before OIDC/Token defaults.

    Passing ``base_classes`` keeps existing authenticators. When omitted, returns
    only WeniAuthentication.
    """
    classes = list(base_classes) if base_classes is not None else []
    if WeniAuthentication not in classes:
        classes.insert(0, WeniAuthentication)
    return classes


def query_params_with_auth_project_uuid(
    request: Request,
    data: Mapping | None = None,
    *,
    project_key: str = "project_uuid",
) -> MutableMapping:
    """
    Return a mutable copy of query/body data with tenant forced from auth.

    JWT callers carry an immutable ``project_uuid`` in the token. Overwriting
    the request value prevents path/query spoofing. Keycloak callers get the
    same key from the standardized resolver, so the value is consistent.
    """
    source = data if data is not None else request.query_params
    mutable = source.copy()
    auth = get_auth_context(request)
    if auth is not None and auth.has_project_uuid:
        mutable[project_key] = str(auth.project_uuid)
    return mutable
