from rest_framework import mixins, viewsets

from insights.authentication.permissions import WidgetAuthPermission

from .models import Widget
from .serializers import WidgetSerializer


class WidgetListUpdateViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
):
    permission_classes = [WidgetAuthPermission]
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer
