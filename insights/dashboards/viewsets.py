from rest_framework import mixins, viewsets

from insights.authentication.permissions import ProjectAuthPermission

from insights.dashboards.models import Dashboard
from .serializers import DashboardSerializer

from insights.dashboards.utils import DefaultPagination


class DashboardViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [ProjectAuthPermission]
    serializer_class = DashboardSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        queryset = Dashboard.objects
        project_id = self.request.query_params.get("project", None)
        if project_id is not None:
            queryset = queryset.filter(project_id=project_id)
            return queryset
        return {}
