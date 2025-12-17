from contextlib import suppress
from django.db import models, transaction
from model_utils import FieldTracker

from insights.shared.models import BaseModel, ConfigurableModel


HUMAN_SERVICE_DASHBOARD_V1_NAME = "Atendimento humano"
HUMAN_SERVICE_DASHBOARD_V2_NAME = "human_support_dashboard.title"
CONVERSATIONS_DASHBOARD_NAME = "conversations_dashboard.title"

PROTECTED_DASHBOARD_NAMES = [
    CONVERSATIONS_DASHBOARD_NAME,
    HUMAN_SERVICE_DASHBOARD_V1_NAME,
    HUMAN_SERVICE_DASHBOARD_V2_NAME,
]


class DashboardTemplate(BaseModel, ConfigurableModel):
    name = models.CharField("Name", max_length=255)
    description = models.TextField("Description", null=True, blank=True)
    project = models.ForeignKey(
        "projects.Project",
        related_name="dashboard_templates",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name}"


class Dashboard(BaseModel, ConfigurableModel):
    project = models.ForeignKey(
        "projects.Project", related_name="dashboards", on_delete=models.CASCADE
    )
    name = models.CharField("Name", max_length=255)
    description = models.TextField("Description")
    is_default = models.BooleanField("Is default?", default=False)
    from_template = models.BooleanField("Came from a template?", default=False)
    template = models.ForeignKey(
        DashboardTemplate,
        related_name="dashboards",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    grid = models.JSONField("Grid", default=list)
    is_deletable = models.BooleanField("Is detetable?", default=False)
    is_editable = models.BooleanField("Is editable?", default=False)

    tracker = FieldTracker(fields=["name"])

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "is_default"],
                condition=models.Q(is_default=True),
                name="unique_default_dashboard_per_project",
            )
        ]

    def save(self, *args, **kwargs):
        if self._state.adding or self.tracker.has_changed("name"):
            if self.name == CONVERSATIONS_DASHBOARD_NAME:
                existing_dashboards = Dashboard.objects.filter(
                    project=self.project,
                    name=CONVERSATIONS_DASHBOARD_NAME,
                )

                if self._state.adding:
                    existing_dashboards = existing_dashboards.exclude(pk=self.pk)

                if existing_dashboards.exists():
                    raise ValueError(
                        "Conversation dashboard already exists for this project"
                    )

        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_default:
            with transaction.atomic():
                deleted = super().delete(using, keep_parents)

                with suppress(Dashboard.DoesNotExist):
                    human_service_dashboard = Dashboard.objects.get(
                        project=self.project, name=HUMAN_SERVICE_DASHBOARD_V1_NAME
                    )
                    human_service_dashboard.is_default = True
                    human_service_dashboard.save(update_fields=["is_default"])

                return deleted

        return super().delete(using, keep_parents)
