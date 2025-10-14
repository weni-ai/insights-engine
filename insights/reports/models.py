from django.db import models
from django.utils.translation import gettext_lazy as _

from insights.shared.models import BaseModel, ConfigurableModel
from insights.reports.choices import ReportStatus, ReportFormat, ReportSource
from insights.users.models import User
from insights.projects.models import Project


class Report(BaseModel, ConfigurableModel):
    """
    This model is used to store the reports.
    """

    project = models.ForeignKey(
        Project, verbose_name=_("Project"), on_delete=models.CASCADE
    )
    source = models.CharField(_("Source"), max_length=255, choices=ReportSource.choices)
    source_config = models.JSONField(_("Source config"), null=True, blank=True)
    filters = models.JSONField(_("Filters"), null=True, blank=True)
    format = models.CharField(_("Format"), max_length=255, choices=ReportFormat.choices)
    status = models.CharField(
        _("Status"),
        max_length=255,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
    )
    requested_by = models.ForeignKey(
        User, verbose_name=_("Requested by"), on_delete=models.SET_NULL, null=True
    )
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    errors = models.JSONField(_("Errors"), null=True, blank=True)

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.uuid} - {self.source} - {self.format} - {self.status}"
