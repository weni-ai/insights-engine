from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.dashboards.models import Dashboard
from insights.dashboards.utils import DefaultPagination
from insights.widgets.models import Widget

from .serializers import (
    DashboardIsDefaultSerializer,
    DashboardSerializer,
    DashboardWidgetsSerializer,
)


class DashboardViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [ProjectAuthPermission]
    serializer_class = DashboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        project_id = self.request.query_params.get("project", None)
        if project_id is not None:
            return Dashboard.objects.filter(project_id=project_id)
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

        widgets = Widget.objects.filter(dashboard=dashboard)

        paginator = DefaultPagination()
        result_page = paginator.paginate_queryset(widgets, request)

        serializer = DashboardWidgetsSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
