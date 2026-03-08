import logging

import requests
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insights.authentication.authentication import StaticTokenAuthentication
from insights.authentication.permissions import (
    IsServiceAuthentication,
    ProjectAuthPermission,
)
from insights.core.urls.proxy_pagination import (
    get_cursor_based_pagination_urls,
)
from insights.human_support.clients.chats import ChatsClient
from insights.projects.dataclass import TicketID
from insights.projects.models import Project
from insights.projects.parsers import parse_dict_to_json
from insights.projects.serializers import (
    ListContactsQueryParamsSerializer,
    ListTicketIDsQueryParamsSerializer,
    ProjectSerializer,
    TicketIDSerializer,
)
from insights.shared.viewsets import get_source
from insights.sources.chats.clients import ChatsRESTClient
from insights.sources.custom_status.client import CustomStatusRESTClient

logger = logging.getLogger(__name__)


class ProjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="sources/(?P<source_slug>[^/.]+)/search",
    )
    def retrieve_source_data(self, request, source_slug=None, *args, **kwargs):
        # Handle special cases for filter endpoints
        if source_slug == "contacts":
            return self.search_contacts(request, *args, **kwargs)
        elif source_slug == "ticket_id":
            return self.search_ticket_ids(request, *args, **kwargs)
        elif source_slug == "custom_status":
            return self.search_custom_status_types(request, *args, **kwargs)

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

            rollback_needed = False
            webhook_error = False
            project.is_allowed = True
            project.save()

            try:
                project.is_allowed = True
                project.save()
                rollback_needed = True

                webhook_url = settings.WEBHOOK_URL
                payload = {"project_uuid": project_uuid}
                headers = {"Authorization": f"Bearer {settings.STATIC_TOKEN}"}

                response = requests.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()

                rollback_needed = False

            except requests.exceptions.RequestException as error:
                logger.error(f"Failed to call webhook: {error}")
                webhook_error = True
                raise
            except Exception as error:
                logger.error(f"Error during webhook process: {error}")
                raise
            finally:
                if rollback_needed:
                    try:
                        project.is_allowed = original_is_allowed
                        project.save()
                        logger.info(
                            f"Rolled back is_allowed status for project {project_uuid}"
                        )
                    except Exception as rollback_error:
                        logger.error(
                            f"Critical: Failed to rollback project state for {project_uuid}: {rollback_error}"
                        )

            if webhook_error:
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

    @action(
        detail=True,
        methods=["get"],
        url_path="filters/contacts",
    )
    def search_contacts(self, request, *args, **kwargs):
        project = self.get_object()

        query_params = ListContactsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        chats_params = query_params.validated_data.copy()
        chats_params["project"] = str(project.uuid)

        chats_client = ChatsClient()
        response = chats_client.get_contacts(query_params=chats_params)

        pagination_urls = get_cursor_based_pagination_urls(request, response)

        return Response(
            {
                "next": pagination_urls.next_url,
                "previous": pagination_urls.previous_url,
                "results": response.get("results"),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="filters/ticket_id",
    )
    def search_ticket_ids(self, request, *args, **kwargs):
        project = self.get_object()

        query_params = ListTicketIDsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        chats_params = query_params.validated_data.copy()
        chats_params["project"] = str(project.uuid)

        chats_client = ChatsClient()
        response = chats_client.get_protocols(query_params=chats_params)
        ticket_ids = [
            TicketID(protocol["protocol"]) for protocol in response.get("results")
        ]

        pagination_urls = get_cursor_based_pagination_urls(request, response)

        return Response(
            {
                "next": pagination_urls.next_url,
                "previous": pagination_urls.previous_url,
                "results": TicketIDSerializer(ticket_ids, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="filters/custom_status",
    )
    def search_custom_status_types(self, request, *args, **kwargs):
        project = self.get_object()
        client = CustomStatusRESTClient(project)
        results = client.list_custom_status_types()
        return Response(results, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="verify_csat",
    )
    def verify_csat(self, request, *args, **kwargs):
        project = self.get_object()
        chats_client = ChatsRESTClient()

        project_data = chats_client.get_project(str(project.uuid))
        is_csat_enabled = project_data.get("is_csat_enabled", False)

        return Response(is_csat_enabled, status=status.HTTP_200_OK)
