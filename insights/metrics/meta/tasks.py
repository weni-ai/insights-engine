from uuid import UUID
from insights.celery import app
import logging
from datetime import datetime

from django.conf import settings

from insights.metrics.meta.services import MetaMessageTemplatesService
from insights.dashboards.models import Dashboard
from sentry_sdk import capture_exception
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from insights.projects.models import Project

logger = logging.getLogger(__name__)


WAIT_TIME_FOR_CHECKING_MARKETING_MESSAGES_STATUS = (
    settings.WAIT_TIME_FOR_CHECKING_MARKETING_MESSAGES_STATUS
)


@app.task
def check_dashboards_marketing_messages_status_for_project(project_uuid: UUID):

    project = Project.objects.get(uuid=project_uuid)

    dashboards = Dashboard.objects.filter(
        Q(project=project)
        & (
            Q(config__is_whatsapp_integration=True)
            & (
                Q(config__is_mm_lite_active=False)
                | Q(config__is_mm_lite_active__isnull=True)
            )
        )
    )

    for dashboard in dashboards:
        config: dict = dashboard.config or {}
        marketing_messages_status_last_checked_at = config.get(
            "marketing_messages_status_last_checked_at"
        )

        if marketing_messages_status_last_checked_at:
            try:
                dt = datetime.fromisoformat(marketing_messages_status_last_checked_at)

                if dt > timezone.now() - timedelta(minutes=15):
                    continue

            except Exception as e:
                event_id = capture_exception(e)
                logger.error(
                    f"Error parsing marketing messages status last checked at: {marketing_messages_status_last_checked_at}. Event ID: {event_id}",
                    exc_info=True,
                )
                continue

        check_marketing_messages_status.apply_async(
            args=[dashboard.uuid],
            expires=timezone.now() + timedelta(minutes=59),
        )


@app.task
def check_marketing_messages_status(dashboard_uuid: UUID):
    """
    Check the meta metrics.
    """
    try:
        dashboard = Dashboard.objects.get(uuid=dashboard_uuid)
    except Dashboard.DoesNotExist as e:
        event_id = capture_exception(e)
        logger.error(
            f"Dashboard {dashboard_uuid} not found. Event ID: {event_id}", exc_info=True
        )

        return

    config: dict = dashboard.config or {}
    is_whatsapp_integration = config.get("is_whatsapp_integration", False)
    waba_id = config.get("waba_id")

    if not is_whatsapp_integration or not waba_id:
        logger.error(
            f"Dashboard {dashboard_uuid} is not a WhatsApp integration or missing waba_id",
            exc_info=True,
        )

        return

    service = MetaMessageTemplatesService()

    is_active = service.check_marketing_messages_status(waba_id=waba_id)

    dashboard.refresh_from_db(fields=["config"])
    config = dashboard.config or {}
    config["is_mm_lite_active"] = is_active
    config["marketing_messages_status_last_checked_at"] = timezone.now().isoformat()
    dashboard.config = config
    dashboard.save(update_fields=["config"])
