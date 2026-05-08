from django.db.models.signals import post_save
from django.dispatch import receiver

from insights.reports.models import Report
from insights.reports.usecases.report_status_cache import ReportStatusCacheUseCase


@receiver(post_save, sender=Report)
def invalidate_report_status_cache(sender, instance, **kwargs):
    ReportStatusCacheUseCase.invalidate(str(instance.project_id))
