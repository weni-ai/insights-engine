import logging

import requests
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.authentication import StaticTokenAuthentication
from insights.authentication.permissions import (
    IsServiceAuthentication,
    ProjectAuthPermission,
)
from insights.projects.models import Project
from insights.projects.parsers import parse_dict_to_json
from insights.shared.viewsets import get_source

logger = logging.getLogger(__name__)


class ProjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [ProjectAuthPermission]
    queryset = Project.objects.all()

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="sources/(?P<source_slug>[^/.]+)/search",
    )
    def retrieve_source_data(self, request, source_slug=None, *args, **kwargs):
        SourceQuery = get_source(slug=source_slug)
        query_kwargs = {}
        if SourceQuery is None:
            return Response(
                {"detail": f"could not find a source with the slug {source_slug}"},
                status.HTTP_404_NOT_FOUND,
            )
        filters = dict(request.data or request.query_params or {})
        operation = filters.pop("operation", ["list"])[0]
        if operation == "list":
            tags = filters.pop("tags", [None])[0]
            if tags:
                filters["tags"] = tags.split(",")
        op_field = filters.pop("op_field", [None])[0]
        if op_field:
            query_kwargs["op_field"] = op_field
        filters["project"] = str(self.get_object().uuid)
        try:
            serialized_source = SourceQuery.execute(
                filters=filters,
                operation=operation,
                parser=parse_dict_to_json,
                user_email=self.request.user.email,
                return_format="select_input",
                query_kwargs=query_kwargs,
            )
        except Exception as error:
            logger.exception(f"Error executing source query: {error}")
            return Response(
                {"detail": "Failed to retrieve source data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(serialized_source, status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="verify_project_indexer")
    def verify_project_indexer(self, request, source_slug=None, *args, **kwargs):

        project = Project.objects.get(pk=self.kwargs["pk"])

        if str(project.pk) in settings.PROJECT_ALLOW_LIST or project.is_allowed:
            return Response(True)

        return Response(False)

    @action(detail=False, methods=["post"], url_path="release_flows_dashboard")
    def release_flows_dashboard(self, request, *args, **kwargs):
        try:
            project_uuid = request.data.get("project_uuid")
            if not project_uuid:
                return Response(
                    {"detail": "project_uuid is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            project = Project.objects.get(uuid=project_uuid)

            original_is_allowed = project.is_allowed

            project.is_allowed = True
            project.save()

            webhook_url = settings.WEBHOOK_URL
            payload = {"project_uuid": project_uuid}
            headers = {"Authorization": f"Bearer {settings.STATIC_TOKEN}"}
            try:
                response = requests.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as error:
                logger.error(f"Failed to call webhook: {error}")
                project.is_allowed = original_is_allowed
                project.save()
                return Response(
                    {"detail": "Failed to process webhook request"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response({"success": True}, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response(
                {"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as exception:
            logger.error(f"Error updating project: {str(exception)}", exc_info=True)
            return Response(
                {"detail": "An internal error occurred while processing your request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["get"],
        url_path="get_allowed_projects",
        authentication_classes=[StaticTokenAuthentication],
        permission_classes=[IsServiceAuthentication],
    )
    def get_allowed_projects(self, request, *args, **kwargs):
        projects = Project.objects.filter(is_allowed=True).values("uuid")
        return Response(list(projects), status=status.HTTP_200_OK)
