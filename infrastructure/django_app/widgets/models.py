from django.db import models

from django_app.db.models import BaseModel, ConfigurableModel


class Widget(BaseModel, ConfigurableModel):
    dashboard = models.UUIDField(primary_key=True)
    source = models.UUIDField(primary_key=True)
    description = models.TextField()
    is_template = models.BooleanField(default=False)
    w_type = models.CharField(max_length=50)
    report = models.JSONField(default={})

    def __str__(self):
        return f"{self.uuid}"
