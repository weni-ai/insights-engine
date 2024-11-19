from rest_framework import mixins, viewsets
from rest_framework.response import Response

from insights.authentication.permissions import WidgetAuthPermission

from .models import Report, Widget
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
            config.update(update_data["config"])
            update_data["config"] = config

        if widget.type not in ["card", "recurrence"]:
            print("entrou no if do type card e recurrence")
            serializer = self._update(widget, update_data, partial)
            return Response(serializer.data)

        if config.get("operation") != "recurrence":
            print("entrou no if co operation")
            try:
                widget.report.delete()
            except Report.DoesNotExist:
                pass
            serializer = self._update(widget, update_data, partial)
            return Response(serializer.data)

        config["limit"] = 1

        if widget.type == "recurrence":
            print("if do type que seta o limite")
            config["limit"] = 5

        serializer = self._update(widget, update_data, partial)
        widget.refresh_from_db()
        try:
            report = widget.report
        except Report.DoesNotExist:
            report = Report(
                widget=widget,
                source=widget.source,
                type="graph_bar",
            )
        print("dentro do codigo que cria o report")
        if report_name:
            print(report_name)
            report.name = report_name

        report.config = {
            "operation": widget.config.get("operation"),
            "op_field": widget.config.get("op_field"),
            "filter": widget.config.get("filter"),
            "data_suffix": "%",
        }

        print("a config do report", report.config)
        report.save()

        return Response(serializer.data)
