from typing import Any
from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from insights.shared.managers import SoftDeletableManager


class UUIDModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=True)

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


class SoftDeletableModel(models.Model):
    is_deleted = models.BooleanField(_("is deleted?"), default=False)

    objects = SoftDeletableManager()
    all_objects = SoftDeletableManager(include_deleted=True)

    class Meta:
        abstract = True

    def deleted_sufix(self):
        return "_is_deleted_" + str(timezone.now())

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        if hasattr(self, "name"):
            self.name += self.deleted_sufix()
        self.save()


class ConfigurableModel(models.Model):
    config = models.JSONField(_("config"), blank=True, null=True)

    class Meta:
        abstract = True

    def get_config(self, key: str, default: Any = None) -> Any:
        return (
            self.config.get(key, default)
            if self.config and isinstance(self.config, dict)
            else default
        )


class BaseModel(UUIDModel, DateTimeModel):
    class Meta:
        abstract = True
