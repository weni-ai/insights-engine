from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from insights.shared.models import BaseModel, ConfigurableModel


class BaseWidget(BaseModel, ConfigurableModel):
    name = models.CharField("Name", max_length=255, null=False, blank=True, default="")
    type = models.CharField(
        "Widget Type", max_length=50, null=True, blank=True, default=None
    )
    source = models.CharField(
        "Data Source", max_length=50, null=True, blank=True, default=None
    )
    # config needs to be required in widget
    config = models.JSONField("Widget Configuration", blank=True, default=dict)

    class Meta:
        abstract = True

    @property
    def is_crossing_data(self):
        return self.config.get("config_type", "default") == "crossing_data"


class Widget(BaseWidget):
    dashboard = models.ForeignKey(
        "dashboards.Dashboard",
        related_name="widgets",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    position = models.JSONField("Widget position", blank=True, default=dict)
    parent = models.ForeignKey(
        "widgets.Widget",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(parent__isnull=True) & Q(dashboard__isnull=False))
                    | (Q(parent__isnull=False) & Q(dashboard__isnull=True))
                ),
                name="widget_parent_xor_dashboard",
                violation_error_message="Widget cannot have both parent and dashboard.",
            ),
        ]

    def clean(self):
        super().clean()

        if self.parent_id and self.parent.parent:
            raise ValidationError(
                "A widget that has a parent cannot have a grandparent.",
                code="widget_parent_cannot_have_a_grandparent",
            )

        if self.pk:
            widget_from_db = Widget.objects.filter(pk=self.pk).first()

            if widget_from_db:
                is_adding_parent = self.parent_id and widget_from_db.parent_id is None

                if is_adding_parent and self.children.exists():
                    raise ValidationError(
                        "A widget that is being added to a parent cannot have children.",
                        code="widget_being_added_to_parent_cannot_have_children",
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def project(self):
        return getattr(self.dashboard, "project", getattr(self.parent, "project", None))

    @property
    def is_configurable(self):
        return self.dashboard.name != "Atendimento humano"

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
            config.get("op_sub_field", None),
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
            config.get("op_sub_field", None),
            config.get("limit", None),
        )
