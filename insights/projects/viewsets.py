import logging
from urllib.parse import urlencode

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
from insights.authentication.services.project_auth import is_project_viewer
from insights.core.urls.proxy_pagination import (
    get_cursor_based_pagination_urls,
    get_limit_offset_pagination_urls,
)
from insights.dashboards.models import CTWA_DASHBOARD_NAME, Dashboard
from insights.dashboards.tasks import check_and_create_ctwa_dashboard
from insights.human_support.clients.chats import ChatsClient
from insights.metrics.ctwa.serializers import (
    CTWACampaignPerformanceSerializer,
    CTWAConversionsSerializer,
    CTWADataQueryParamsSerializer,
    CTWADataSerializer,
    CTWAPerformanceByCampaignQueryParamsSerializer,
)
from insights.metrics.ctwa.services import CTWADashboardService
from insights.projects.dataclass import TicketID
from insights.projects.models import Project, ProjectAuth
from insights.projects.services.indexer_activation import is_project_indexer_active
from insights.projects.parsers import parse_dict_to_json
from insights.projects.serializers import (
    ListContactsQueryParamsSerializer,
    ListTicketIDsQueryParamsSerializer,
    MetaCampaignQueryParamsSerializer,
    MetaCampaignSerializer,
    ProjectSerializer,
    TicketIDSerializer,
)
from insights.shared.viewsets import get_source
from insights.sources.agents.usecases.query_execute import (
    ProjectAdminsAndManagersQueryExecutor,
)
from insights.sources.chats.clients import ChatsRESTClient
from insights.sources.custom_status.client import CustomStatusRESTClient
from insights.sources.meta.campaign.usecases.query_execute import (
    QueryExecutor as MetaCampaignQueryExecutor,
)

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

    @action(
        detail=True,
        methods=["get"],
        url_path="sources/meta/campaign",
    )
    def list_meta_campaigns(self, request, *args, **kwargs):
        project = self.get_object()
        query_params = MetaCampaignQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        filters = {
            "project": str(project.uuid),
            **query_params.validated_data,
        }

        try:
            source_data = MetaCampaignQueryExecutor.execute(
                filters=filters,
                operation="list",
                parser=parse_dict_to_json,
            )
        except Exception as error:
            logger.exception(f"Error listing Meta campaigns: {error}")
            return Response(
                {"detail": "Failed to retrieve source data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        pagination_urls = get_limit_offset_pagination_urls(request, source_data)

        return Response(
            {
                "count": source_data.get("count", 0),
                "next": pagination_urls.next_url,
                "previous": pagination_urls.previous_url,
                "results": MetaCampaignSerializer(
                    source_data.get("results", []), many=True
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="ctwa/data",
    )
    def ctwa_data(self, request, *args, **kwargs):
        project = self.get_object()
        query_params = CTWADataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        try:
            data = CTWADashboardService().get_data(
                project_uuid=str(project.uuid),
                start_date=query_params.validated_data["start_date"],
                end_date=query_params.validated_data["end_date"],
                campaign=query_params.validated_data.get("campaign"),
            )
        except Exception as error:
            logger.exception(f"Error retrieving CTWA data: {error}")
            return Response(
                {"detail": "Failed to retrieve CTWA data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(CTWADataSerializer(data).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="ctwa/conversions",
    )
    def ctwa_conversions(self, request, *args, **kwargs):
        project = self.get_object()
        query_params = CTWADataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        try:
            data = CTWADashboardService().get_conversions(
                project_uuid=str(project.uuid),
                start_date=query_params.validated_data["start_date"],
                end_date=query_params.validated_data["end_date"],
                campaign=query_params.validated_data.get("campaign"),
            )
        except Exception as error:
            logger.exception(f"Error retrieving CTWA conversions: {error}")
            return Response(
                {"detail": "Failed to retrieve CTWA conversions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            CTWAConversionsSerializer(data).data, status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="ctwa/performance_by_campaign",
    )
    def ctwa_performance_by_campaign(self, request, *args, **kwargs):
        project = self.get_object()
        query_params = CTWAPerformanceByCampaignQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)

        limit = query_params.validated_data["limit"]
        offset = query_params.validated_data["offset"]

        try:
            data = CTWADashboardService().get_performance_by_campaign(
                project_uuid=str(project.uuid),
                start_date=query_params.validated_data["start_date"],
                end_date=query_params.validated_data["end_date"],
                limit=limit,
                offset=offset,
                campaign=query_params.validated_data.get("campaign"),
            )
        except Exception as error:
            logger.exception(f"Error retrieving CTWA performance by campaign: {error}")
            return Response(
                {"detail": "Failed to retrieve CTWA performance by campaign"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        count = data.get("count", 0)
        next_offset = offset + limit
        previous_offset = max(offset - limit, 0)

        return Response(
            {
                "count": count,
                "next": self._ctwa_limit_offset_url(request, query_params, next_offset)
                if next_offset < count
                else None,
                "previous": self._ctwa_limit_offset_url(
                    request, query_params, previous_offset
                )
                if offset > 0
                else None,
                "currency": data.get("currency"),
                "results": CTWACampaignPerformanceSerializer(
                    data.get("results", []), many=True
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def _ctwa_limit_offset_url(self, request, query_params, offset):
        params = {
            "start_date": query_params.validated_data["start_date"].isoformat(),
            "end_date": query_params.validated_data["end_date"].isoformat(),
            "limit": query_params.validated_data["limit"],
            "offset": offset,
        }
        campaign = query_params.validated_data.get("campaign")
        if campaign:
            params["campaign"] = campaign
        return request.build_absolute_uri(f"{request.path}?{urlencode(params)}")

    @action(detail=True, methods=["get"], url_path="verify_project_indexer")
    def verify_project_indexer(self, request, source_slug=None, *args, **kwargs):

        project = Project.objects.get(pk=self.kwargs["pk"])

        return Response(is_project_indexer_active(project))

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

        chats_client = ChatsClient(project)
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

        chats_client = ChatsClient(project)
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
        url_path="filters/project_managers",
    )
    def search_project_managers(self, request, *args, **kwargs):
        project = self.get_object()

        filters = dict(request.query_params or {})
        tags = filters.pop("tags", [None])[0]
        if tags:
            filters["tags"] = tags.split(",")
        filters["project"] = str(project.uuid)

        try:
            serialized_source = ProjectAdminsAndManagersQueryExecutor.execute(
                filters=filters,
                operation="list",
                parser=parse_dict_to_json,
                user_email=self.request.user.email,
                return_format="select_input",
            )
        except Exception as error:
            logger.exception(f"Error executing project managers query: {error}")
            return Response(
                {"detail": "Failed to retrieve source data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serialized_source, status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="verify_ctwa",
    )
    def verify_ctwa(self, request, *args, **kwargs):
        project = self.get_object()
        exists = Dashboard.objects.filter(
            project=project, name=CTWA_DASHBOARD_NAME
        ).exists()

        queued = False
        if not exists and settings.ENABLE_CTWA_DASHBOARD_AUTO_CREATION:
            check_and_create_ctwa_dashboard.delay(str(project.uuid))
            queued = True

        return Response(
            {"exists": exists, "queued": queued},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="verify_csat",
    )
    def verify_csat(self, request, *args, **kwargs):
        project = self.get_object()
        chats_client = ChatsRESTClient(project)

        project_data = chats_client.get_project()
        is_csat_enabled = project_data.get("is_csat_enabled", False)

        return Response(is_csat_enabled, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="verify_viewer",
        permission_classes=[IsAuthenticated],
    )
    def verify_viewer(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(pk=self.kwargs["pk"])
        except Project.DoesNotExist:
            return Response(False, status=status.HTTP_200_OK)

        if ProjectAuth.objects.filter(
            user=request.user, project=project, role=1
        ).exists():
            return Response(False, status=status.HTTP_200_OK)

        token = request.headers.get("Authorization")
        if not token:
            return Response(False, status=status.HTTP_200_OK)

        return Response(
            is_project_viewer(token, str(project.uuid)),
            status=status.HTTP_200_OK,
        )
