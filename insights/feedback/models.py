from django.db import models
from django.utils import timezone

from insights.shared.models import BaseModel


class SurveyCycle(BaseModel):
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        verbose_name = _("Survey Cycle")
        verbose_name_plural = _("Survey Cycles")

    @property
    def is_active(self) -> bool:
        return self.start <= timezone.now() <= self.end
