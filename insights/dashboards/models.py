from django.db import models

from insights.shared.models import BaseModel, ConfigurableModel


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

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "is_default",
                ],
                condition=models.Q(is_default=True),
                name="unique_true_default_dashboard",
            )
        ]
