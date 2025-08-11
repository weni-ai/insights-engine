from django.db import models
from django.utils.translation import gettext_lazy as _


class ProjectIndexerActivationStatus(models.TextChoices):
    """
    This choice is used to define the status of the indexer activation.
    """

    PENDING = "PENDING", _("Pending")
    SUCCESS = "SUCCESS", _("Success")
    FAILED = "FAILED", _("Failed")
