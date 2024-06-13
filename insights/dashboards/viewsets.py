from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.dashboards.models import Dashboard
from insights.dashboards.utils import DefaultPagination
from insights.widgets.models import Widget, Report

from .serializers import (
    DashboardIsDefaultSerializer,
    DashboardSerializer,
    DashboardWidgetsSerializer,
    ReportSerializer,
)
from .usecases import dashboard_filters


class DashboardViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [ProjectAuthPermission]
    serializer_class = DashboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        project_id = self.request.query_params.get("project", None)
        if project_id is not None:
            return (
                Dashboard.objects.filter(project_id=project_id)
                .exclude(title="Resultados de fluxos")
                .order_by("created_on")
            )
        return Dashboard.objects.none()

    @action(detail=True, methods=["patch"])
    def is_default(self, request, pk=None):
        dashboard = self.get_object()
        serializer = DashboardIsDefaultSerializer(
            dashboard, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=["get"])
    def list_sources(self, request, pk=None):
        dashboard = self.get_object()
        widgets = dashboard.widgets.all()

        sources = [{"source": widget.source} for widget in widgets]

        paginator = DefaultPagination()
        paginated_sources = paginator.paginate_queryset(sources, request)

        return paginator.get_paginated_response(paginated_sources)
