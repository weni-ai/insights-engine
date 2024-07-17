from django.db import models

from insights.shared.models import BaseModel, ConfigurableModel


class BaseWidget(BaseModel, ConfigurableModel):
    name = models.CharField(
        "Name", max_length=255, null=False, blank=False, default=None
    )
    type = models.CharField(
        "Widget Type", max_length=50, null=False, blank=False, default=None
    )
    source = models.CharField(
        "Data Source", max_length=50, null=False, blank=False, default=None
    )
    # config needs to be required in widget
    config = models.JSONField("Widget Configuration")

    class Meta:
        abstract = True


class Widget(BaseWidget):
    dashboard = models.ForeignKey(
        "dashboards.Dashboard", related_name="widgets", on_delete=models.CASCADE
    )
    position = models.JSONField("Widget position")

    def __str__(self):
        return self.name

    @property
    def project(self):
        return self.dashboard.project

    @property
    def is_configurable(self):
        return self.dashboard.name == "Resultados de fluxos"

    def source_config(self, sub_widget: str = None, is_live=False):
        config = self.config if sub_widget is None else self.config[sub_widget]
        # default_filters, operation, op_field, limit
        filters = config.get("filter", {})
        if is_live:
            filters.update(config.get("live_filter", {}))
        return (
            filters,
            config.get("operation", "list"),
            config.get("op_field", None),
            config.get("limit", None),
        )


class Report(BaseWidget):
    widget = models.OneToOneField(
        Widget, related_name="report", on_delete=models.CASCADE
    )

    @property
    def project(self):
        return self.widget.project

    def __str__(self):
        return self.name

    def source_config(self, sub_widget: str = None, is_live=False):
        config = self.config if sub_widget is None else self.config[sub_widget]
        # default_filters, operation, op_field, limit
        filters = config.get("filter", {})
        if is_live:
            filters.update(config.get("live_filter", {}))
        return (
            filters,
            config.get("operation", "list"),
            config.get("op_field", None),
            config.get("limit", None),
        )
