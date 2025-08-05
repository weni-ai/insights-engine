from django.db import models
from django.utils.translation import gettext_lazy as _


class IndexerActivationStatus(models.IntegerChoices):
    PENDING = 0, _("pending")
    ACTIVATED = 1, _("activated")
