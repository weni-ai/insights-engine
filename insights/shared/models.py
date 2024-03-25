from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDModel(models.Model):
    uuid = models.UUIDField(primary_key=True)

    class Meta:
        abstract = True


class DateTimeModel(models.Model):
    created_on = models.DateTimeField(
        _("Created on"), editable=False, auto_now_add=True
    )
    modified_on = models.DateTimeField(_("Modified on"), auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class ConfigurableModel(models.Model):
    config = models.JSONField(_("config"), blank=True, null=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, DateTimeModel):
    class Meta:
        abstract = True
