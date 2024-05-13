from rest_framework import mixins, viewsets

from insights.widgets.permissions import ProjectAuthPermission

from .models import Widget
from .serializers import WidgetSerializer


class WidgetListUpdateViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [ProjectAuthPermission]
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
