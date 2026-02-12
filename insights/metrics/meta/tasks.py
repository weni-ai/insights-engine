from uuid import UUID
from insights.celery import app
import logging

from insights.metrics.meta.services import MetaMessageTemplatesService
from insights.dashboards.models import Dashboard
from sentry_sdk import capture_exception
from django.utils import timezone

logger = logging.getLogger(__name__)


@app.task
def check_meta_metrics(dashboard_uuid: UUID):
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
