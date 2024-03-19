from django.db import models

from insights.db.models import BaseModel, ConfigurableModel, SoftDeleteModel


class Project(BaseModel, ConfigurableModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    is_template = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.uuid} - Project: {self.name}"
