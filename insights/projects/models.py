from django.db import models

from insights.shared.models import (
    BaseModel,
    ConfigurableModel,
    SoftDeleteModel,
)


class Project(BaseModel, ConfigurableModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    is_template = models.BooleanField(default=False)
    timezone = models.CharField(max_length=64, null=True)
    date_format = models.CharField(max_length=64, null=True)
    is_active = models.BooleanField(default=True)
    vtex_account = models.CharField(max_length=100, null=True)
    is_allowed = models.BooleanField(default=False)
    org_uuid = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.uuid} - Project: {self.name}"


class Roles(models.IntegerChoices):
    NOT_SETTED, ADMIN = list(range(2))


class ProjectAuth(BaseModel):
    class Meta:
        unique_together = ["user", "project"]

    project = models.ForeignKey(
        Project, related_name="authorizations", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "users.User",
        related_name="authorizations",
        to_field="email",
        on_delete=models.CASCADE,
    )
    role = models.IntegerField(choices=Roles, default=Roles.NOT_SETTED)

    def __str__(self):
        return f"[{self.role}] {self.project.name} - {self.user.email}"
