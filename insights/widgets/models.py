from django.db import models

from insights.shared.models import BaseModel, ConfigurableModel


class Widget(BaseModel, ConfigurableModel):
    dashboard = models.ForeignKey(
        "dashboards.Dashboard", related_name="widgets", on_delete=models.CASCADE
    )
    name = models.CharField(
        "Name", max_length=255, null=False, blank=False, default=None
    )
    w_type = models.CharField(
        "Widget Type", max_length=50, null=False, blank=False, default=None
    )
    source = models.CharField(
        "Data Source", max_length=50, null=False, blank=False, default=None
    )
    position = models.JSONField("Widget position")
    config = models.JSONField("Widget Configuration")
    report = models.JSONField("Widget Report")

    def __str__(self):
        return self.description
