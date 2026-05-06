from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthPermission
from insights.core.filters import get_filters_from_query_params
from insights.dashboards.api.v1.viewsets import DashboardViewSet
from insights.human_support.services import HumanSupportDashboardService


class DashboardViewSetV2(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]
    get_queryset = DashboardViewSet.get_queryset

    @action(
        detail=True,
        methods=["get"],
        url_path="finished",
    )
    def finished(self, request, pk=None):
        dashboard = self.get_object()
        service = HumanSupportDashboardService(project=dashboard.project)
        filters = get_filters_from_query_params(request.query_params)
        data = service.get_finished_rooms_v2(filters=filters)
        return Response(data, status=status.HTTP_200_OK)
