from django.db import models

from django_app.db.models import BaseModel, ConfigurableModel, SoftDeleteModel


class Project(BaseModel, ConfigurableModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    is_template = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.uuid} - Project: {self.name}"


class ProjectAuth(BaseModel):
    class Meta:
        unique_together = ["user", "project"]

    class Roles(models.IntegerChoices):
        NOT_SETTED, ADMIN = list(range(2))

    project = models.ForeignKey(
        Project, related_name="authorizations", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "accounts.User", related_name="authorizations", on_delete=models.CASCADE
    )
    role = models.IntegerField(choices=Roles, default=Roles.NOT_SETTED)
