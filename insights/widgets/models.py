from django.db import models

from insights.shared.models import BaseModel, ConfigurableModel
from settings import INSIGHTS_DOMAIN


class BaseWidget(BaseModel, ConfigurableModel):
    name = models.CharField(
        "Name", max_length=255, null=False, blank=False, default=None
    )
    w_type = models.CharField(
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
    def url(self):
        if self.config["external_url"]:
            return self.config["external_url"]
        return f"{INSIGHTS_DOMAIN}/dashboards/self.widget.dashboard/widgets/self.widget/report"


class Report(BaseWidget):
    widget = models.OneToOneField(
        Widget, related_name="report", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
