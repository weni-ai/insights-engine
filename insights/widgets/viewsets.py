from rest_framework import mixins, viewsets

from insights.widgets.permissions import ProjectAuthPermission

from .models import Widget
from .serializers import WidgetSerializer


class WidgetListUpdateViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    def get_permissions(self):
        permission_classes = [ProjectAuthPermission]
        return [permission() for permission in permission_classes]

    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
