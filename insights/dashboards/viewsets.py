import logging

from django.conf import settings
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.dashboards.filters import DashboardFilter
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.flows_dashboard_creation import (
    CreateFlowsDashboard,
)
from insights.dashboards.utils import DefaultPagination
from insights.projects.models import Project
from insights.projects.tasks import check_nexus_multi_agents_status
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO
from insights.sources.contacts.clients import FlowsContactsRestClient
from insights.sources.custom_status.client import CustomStatusRESTClient
from insights.widgets.models import Report, Widget
from insights.widgets.usecases.get_source_data import (
    get_source_data_from_widget,
)

from insights.human_support.services import HumanSupportDashboardService
from .serializers import (
    DashboardEditSerializer,
    DashboardIsDefaultSerializer,
    DashboardSerializer,
    DashboardWidgetsSerializer,
    ReportSerializer,
)
from .usecases import dashboard_filters

logger = logging.getLogger(__name__)


class DashboardViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]
    serializer_class = DashboardSerializer
    pagination_class = DefaultPagination

    filter_backends = [DjangoFilterBackend]
    filterset_class = DashboardFilter

    def get_queryset(self):
        queryset = (
            Dashboard.objects.filter(project__authorizations__user=self.request.user)
            .exclude(
                Q(name="Resultados de fluxos")
                & ~Q(project_id__in=settings.PROJECT_ALLOW_LIST)
            )
            .exclude(
                Q(name=CONVERSATIONS_DASHBOARD_NAME)
                & Q(project__is_nexus_multi_agents_active=False),
            )
        )

        if settings.CONVERSATIONS_DASHBOARD_EXCLUDE_FROM_LIST_IF_INDEXER_IS_NOT_ACTIVE:
            queryset = queryset.exclude(
                Q(name=CONVERSATIONS_DASHBOARD_NAME)
                & (
                    Q(project__is_allowed=False)
                    & ~Q(project__uuid__in=settings.PROJECT_ALLOW_LIST)
                )
            )

        queryset = queryset.order_by("created_on")

        return queryset

    def list(self, request, *args, **kwargs):
        if project_uuid := request.query_params.get("project"):
            is_nexus_multi_agents_active = (
                Project.objects.filter(uuid=project_uuid)
                .values_list("is_nexus_multi_agents_active", flat=True)
                .first()
            )

            if not is_nexus_multi_agents_active:
                check_nexus_multi_agents_status.delay(project_uuid)

        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if not instance.is_editable:
            return Response(
                {"This dashboard is not editable."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = DashboardEditSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_deletable:
            return Response(
                {"This dashboard is not deletable."}, status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=["patch"])
    def is_default(self, request, pk=None):
        dashboard: Dashboard = self.get_object()

        serializer = DashboardIsDefaultSerializer(
            dashboard, data=request.data, partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def list_widgets(self, request, pk=None):
        dashboard = self.get_object()

        widgets = Widget.objects.filter(dashboard=dashboard).order_by("created_on")

        paginator = DefaultPagination()
        result_page = paginator.paginate_queryset(widgets, request)

        serializer = DashboardWidgetsSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"])
    def filters(self, request, pk=None):
        dashboard = self.get_object()
        filters = dashboard_filters.get_dash_filters(dashboard)

        return Response(filters)

    @action(
        detail=True, methods=["get"], url_path="widgets/(?P<widget_uuid>[^/.]+)/data"
    )
    def get_widget_data(self, request, pk=None, widget_uuid=None):
        try:
            widget = Widget.objects.get(uuid=widget_uuid, dashboard_id=pk)
            filters = dict(request.data or request.query_params or {})
            filters.pop("project", None)
            is_live = filters.pop("is_live", False)
            serialized_source = get_source_data_from_widget(
                widget=widget,
                is_report=False,
                is_live=is_live,
                filters=filters,
                user_email=request.user.email,
            )
            return Response(serialized_source, status.HTTP_200_OK)
        except Exception as error:
            logger.exception(f"Error loading widget data: {error}")
            return Response(
                {"detail": "Failed to load widget data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True, methods=["get"], url_path="widgets/(?P<widget_uuid>[^/.]+)/report"
    )
    def get_widget_report(self, request, pk=None, widget_uuid=None):
        try:
            widget = Widget.objects.get(uuid=widget_uuid, dashboard_id=pk)
            report = widget.report
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Widget.DoesNotExist:
            return Response(
                {"detail": "Widget not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Report.DoesNotExist:
            return Response(
                {"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=["get"],
        url_path="widgets/(?P<widget_uuid>[^/.]+)/report/data",
    )
    def get_report_data(self, request, pk=None, widget_uuid=None):
        try:
            widget = Widget.objects.get(uuid=widget_uuid, dashboard_id=pk)
            filters = dict(request.data or request.query_params or {})
            filters.pop("project", None)
            is_live = filters.pop("is_live", False)
            serialized_source = get_source_data_from_widget(
                widget=widget,
                is_report=True,
                filters=filters,
                user_email=request.user.email,
                is_live=is_live,
            )
            return Response(serialized_source, status.HTTP_200_OK)
        except Exception as error:
            logger.exception(f"Error loading report data: {error}")
            return Response(
                {"detail": "Failed to load report data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def list_sources(self, request, pk=None):
        dashboard = self.get_object()
        widgets = dashboard.widgets.all()

        sources = [{"source": widget.source} for widget in widgets]

        paginator = DefaultPagination()
        paginated_sources = paginator.paginate_queryset(sources, request)

        return paginator.get_paginated_response(paginated_sources)

    @action(
        detail=True,
        methods=["get"],
        url_path="monitoring/list_status",
    )
    def monitoring_list_status(self, request, pk=None):
        """
        Returns active_rooms, closed_rooms, queue_rooms for the dashboard's project.
        """
        dashboard = self.get_object()
        service = HumanSupportDashboardService(project=dashboard.project)
        data = service.get_attendance_status(filters=request.query_params)
        return Response(data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="monitoring/average_time_metrics",
    )
    def monitoring_average_time_metrics(self, request, pk=None):
        """
        Returns average and max time metrics for the dashboard's project.
        """
        dashboard = self.get_object()
        service = HumanSupportDashboardService(project=dashboard.project)
        data = service.get_time_metrics(filters=request.query_params)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def create_flows_dashboard(self, request, pk=None):
        try:
            project = Project.objects.get(pk=request.query_params.get("project"))
        except Exception as error:
            logger.exception(f"Error creating flows dashboard: {error}")
            return Response(
                {"detail": "Project not found or invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        flow_dashboard = FlowsDashboardCreationDTO(
            project=project,
            dashboard_name=request.data.get("name"),
            funnel_amount=request.data.get("funnel_amount"),
            currency_type=request.data.get("currency_type"),
        )
        create_dashboard_instance = CreateFlowsDashboard(params=flow_dashboard)

        dash = create_dashboard_instance.create_dashboard()
        serialized_data = DashboardSerializer(dash)
        return Response(
            {"dashboard": serialized_data.data},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def get_contacts_results(self, request, pk=None, flow_uuid=None):
        flow_uuid = request.query_params.get("flow_uuid")
        page_number = request.query_params.get("page_number")
        page_size = request.query_params.get("page_size")
        project_uuid = request.query_params.get("project_uuid")
        op_field = request.query_params.get("op_field")
        label = request.query_params.get("label")
        user = request.query_params.get("user_email")
        ended_at_gte = request.query_params.get("ended_at__gte")
        ended_at_lte = request.query_params.get("ended_at__lte")

        flows_contact_client = FlowsContactsRestClient()

        contacts_list = flows_contact_client.get_flows_contacts(
            flow_uuid=flow_uuid,
            page_number=page_number,
            page_size=page_size,
            project_uuid=project_uuid,
            op_field=op_field,
            label=label,
            user=user,
            ended_at_gte=ended_at_gte,
            ended_at_lte=ended_at_lte,
        )
        return Response(contacts_list, status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["get"],
    )
    def get_custom_status(self, request, project=None):
        project = Project.objects.filter(pk=request.query_params.get("project")).first()

        if not project:
            return Response(
                {"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND
            )

        custom_status_client = CustomStatusRESTClient(project)

        query_filters = dict(request.data or request.query_params or {})
        custom_status = custom_status_client.list(query_filters)

        return Response(custom_status, status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="monitoring/peaks_in_human_service",
    )
    def monitoring_peaks_in_human_service(self, request, pk=None):
        """
        Retorna a série de atendimentos por hora (mesmo cálculo do widget).
        """
        dashboard = self.get_object()
        service = HumanSupportDashboardService(project=dashboard.project)
        results = service.get_peaks_in_human_service(filters=request.query_params)
        return Response({"results": results}, status=status.HTTP_200_OK)
