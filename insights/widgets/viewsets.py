from rest_framework import mixins, viewsets
from rest_framework.response import Response
from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthPermission
from insights.projects.models import ProjectAuth
from insights.widgets.permissions import CanCreateWidgetPermission

from insights.widgets.models import Report, Widget
from insights.widgets.serializers import WidgetSerializer


class WidgetViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
):
    queryset = Widget.objects.all()
    serializer_class = WidgetSerializer

    @property
    def permission_classes(self):
        if self.action == "create":
            return [IsAuthenticated, CanCreateWidgetPermission]

        return [IsAuthenticated, ProjectAuthPermission]

    def get_queryset(self) -> QuerySet[Widget]:
        return self.queryset.filter(
            dashboard__project__in=ProjectAuth.objects.filter(
                user=self.request.user, role=1
            ).values_list("project", flat=True)
        )

    def _update(self, widget, update_data, partial):
        serializer = self.get_serializer(widget, data=update_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return serializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        widget = self.get_object()
        update_data = dict(request.data)
        report_name = update_data.pop("report_name", None)

        config = widget.config

        if "config" in update_data:
            config = update_data["config"]

        serializer = self._update(widget, update_data, partial)
        widget.refresh_from_db()

        if widget.type not in {"card", "recurrence"}:
            return Response(serializer.data)

        if config.get("operation") != "recurrence":
            try:
                widget.report.delete()
            except Report.DoesNotExist:
                pass
            return Response(serializer.data)

        if widget.type == "recurrence":
            config["limit"] = min(config.get("limit", 1), 5)
        else:
            config["limit"] = 1

        widget.config = config
        widget.save()

        try:
            report = widget.report
        except Report.DoesNotExist:
            report = Report(
                widget=widget,
                source=widget.source,
                type="graph_bar",
            )

        if report_name:
            report.name = report_name

        report.config = {
            "operation": widget.config.get("operation"),
            "op_field": widget.config.get("op_field"),
            "filter": widget.config.get("filter"),
            "data_suffix": "%",
        }
        report.save()

        return Response(serializer.data)
