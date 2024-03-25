from django.db import models

from django_app.db.models import BaseModel, ConfigurableModel

# Create your models here.


class DashboardTemplate(BaseModel):
    description = models.CharField(max_length=255)
    project = models.models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, null=True, blank=True
    )
    setup = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.uuid} - {self.description}"


class Dashboard(BaseModel, ConfigurableModel):
    project = models.models.ForeignKey("projects.Project", on_delete=models.CASCADE)
    description = models.TextField()
    is_default = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.uuid} - {self.description}"