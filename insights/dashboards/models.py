from contextlib import suppress
from django.db import models, transaction

from insights.shared.models import BaseModel, ConfigurableModel


HUMAN_SERVICE_DASHBOARD_NAME = "Atendimento humano"


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

    def delete(self, using=None, keep_parents=False):
        if self.is_default:
            with transaction.atomic():
                deleted = super().delete(using, keep_parents)

                with suppress(Dashboard.DoesNotExist):
                    human_service_dashboard = Dashboard.objects.get(
                        project=self.project, name=HUMAN_SERVICE_DASHBOARD_NAME
                    )
                    human_service_dashboard.is_default = True
                    human_service_dashboard.save(update_fields=["is_default"])

                return deleted

        deleted = super().delete(using, keep_parents)
