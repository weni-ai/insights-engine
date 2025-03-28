from django.conf import settings
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.projects.models import Project
from insights.dashboards.models import Dashboard
from insights.dashboards.utils import DefaultPagination
from insights.widgets.models import Report, Widget
from insights.widgets.usecases.get_source_data import (
    get_source_data_from_widget,
)

from .serializers import (
    DashboardIsDefaultSerializer,
    DashboardSerializer,
    DashboardWidgetsSerializer,
    ReportSerializer,
    DashboardEditSerializer,
)
from .usecases import dashboard_filters

from insights.dashboards.usecases.flows_dashboard_creation import CreateFlowsDashboard
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO

from insights.sources.contacts.clients import FlowsContactsRestClient
from insights.sources.custom_status.client import CustomStatusRESTClient


class DashboardViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [ProjectAuthPermission]
    serializer_class = DashboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        project_id = self.request.query_params.get("project", None)  # do we need this?
        if project_id is not None:
            return (
                Dashboard.objects.filter(project_id=project_id)
                .exclude(
                    Q(name="Resultados de fluxos")
                    & ~Q(project_id__in=settings.PROJECT_ALLOW_LIST)
                )
                .order_by("created_on")
            )

        return Dashboard.objects.none()

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
        # try:
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
        # except Exception as err:
        #     return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

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
        # try:
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

        # except Exception as err:
        #     return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def list_sources(self, request, pk=None):
        dashboard = self.get_object()
        widgets = dashboard.widgets.all()

        sources = [{"source": widget.source} for widget in widgets]

        paginator = DefaultPagination()
        paginated_sources = paginator.paginate_queryset(sources, request)

        return paginator.get_paginated_response(paginated_sources)

    @action(detail=False, methods=["post"])
    def create_flows_dashboard(self, request, pk=None):
        try:
            project = Project.objects.get(pk=request.query_params.get("project"))
        except Exception as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

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
        project = Project.objects.get(pk=request.query_params.get("project"))
        custom_status_client = CustomStatusRESTClient(project)

        query_filters = dict(request.data or request.query_params or {})
        custom_status = custom_status_client.list(query_filters)

        return Response(custom_status, status.HTTP_200_OK)
