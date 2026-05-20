from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404

from insights.authentication.services.project_auth import (
    has_external_general_project_permission,
)
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.projects.models import Project, ProjectAuth


def is_local_admin(user, *, project=None, project_uuid=None) -> bool:
    qs = ProjectAuth.objects.filter(user=user, role=1)
    if project is not None:
        qs = qs.filter(project=project)
    else:
        qs = qs.filter(project__uuid=project_uuid)
    return qs.exists()


def has_project_read_access(request, project_uuid) -> bool:
    """
    Read access is granted only to Insights local admins (ProjectAuth.role=1)
    or Connect project viewers (external authorization on safe methods).
    """
    user = request.user
    if user.is_anonymous:
        return False

    project_uuid = str(project_uuid)

    if is_local_admin(user, project_uuid=project_uuid):
        return True

    return has_external_general_project_permission(request, project_uuid)


def resolve_project_uuid_from_request(
    request, *, dashboard_pk=None, widget_pk=None
) -> str | None:
    project_uuid = request.query_params.get("project") or request.query_params.get(
        "project_uuid"
    )
    if project_uuid:
        return str(project_uuid)

    if dashboard_pk:
        resolved = (
            Dashboard.objects.filter(uuid=dashboard_pk)
            .values_list("project__uuid", flat=True)
            .first()
        )
        if resolved:
            return str(resolved)

    if widget_pk:
        from insights.widgets.models import Widget

        resolved = (
            Widget.objects.filter(uuid=widget_pk)
            .values_list("dashboard__project__uuid", flat=True)
            .first()
        )
        if resolved:
            return str(resolved)

    return None


def get_project_with_read_access(request, project_uuid: str) -> Project:
    project = get_object_or_404(Project, uuid=project_uuid)
    if not has_project_read_access(request, str(project.uuid)):
        raise Http404
    return project


def apply_dashboard_visibility_excludes(queryset: QuerySet) -> QuerySet:
    queryset = queryset.exclude(
        Q(name="Resultados de fluxos")
        & ~Q(project_id__in=settings.PROJECT_ALLOW_LIST)
    ).exclude(
        Q(name=CONVERSATIONS_DASHBOARD_NAME)
        & Q(project__is_nexus_multi_agents_active=False),
    )

    if settings.CONVERSATIONS_DASHBOARD_EXCLUDE_FROM_LIST_IF_INDEXER_IS_NOT_ACTIVE:
        queryset = queryset.exclude(
            Q(name=CONVERSATIONS_DASHBOARD_NAME)
            & (
                Q(project__is_allowed=False)
                & ~Q(project__uuid__in=settings.PROJECT_ALLOW_LIST)
            )
        )

    return queryset


def get_dashboard_queryset_for_request(
    request, *, dashboard_pk=None, widget_pk=None
) -> QuerySet:
    queryset = apply_dashboard_visibility_excludes(Dashboard.objects.all())

    access_filter = Q(
        project__authorizations__user=request.user,
        project__authorizations__role=1,
    )

    project_uuid = resolve_project_uuid_from_request(
        request, dashboard_pk=dashboard_pk, widget_pk=widget_pk
    )
    if project_uuid and has_external_general_project_permission(
        request, project_uuid
    ):
        access_filter |= Q(project__uuid=project_uuid)

    return queryset.filter(access_filter).distinct().order_by("created_on")
