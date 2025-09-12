from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportSource(models.TextChoices):
    """
    This choice is used to define the source of the report
    """

    CONVERSATIONS_DASHBOARD = "CONVERSATIONS_DASHBOARD", _("Conversations dashboard")


class ReportFormat(models.TextChoices):
    """
    This choice is used to define the output format of the report.
    """

    CSV = "CSV", _("CSV")
    XLSX = "XLSX", _("XLSX")


class ReportStatus(models.TextChoices):
    """
    This choice is used to define the status of the report.
    """

    PENDING = "PENDING", _("Pending")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    READY = "READY", _("Ready")
    FAILED = "FAILED", _("Failed")
