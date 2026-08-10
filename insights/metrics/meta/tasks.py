from copy import deepcopy
from uuid import UUID
from insights.celery import app
import logging
from datetime import datetime

from django.conf import settings

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.services import MetaMessageTemplatesService
from insights.metrics.meta.usecases.waba_migration_analytics import (
    resolve_new_template_id,
)
from insights.dashboards.models import Dashboard
from insights.widgets.models import Widget
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


@app.task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    retry_backoff=True,
)
def move_favorite_templates(
    old_dashboard_uuid: UUID | str,
    new_dashboard_uuid: UUID | str,
):
    """
    After a WABA migration, copy favorite templates from the old dashboard to
    the new one, resolving template ids on the new WABA by exact name match.
    """
    from insights.metrics.meta.usecases.move_favorite_templates import (
        MoveFavoriteTemplatesUseCase,
    )

    try:
        moved = MoveFavoriteTemplatesUseCase().execute(
            old_dashboard_uuid=old_dashboard_uuid,
            new_dashboard_uuid=new_dashboard_uuid,
        )
        logger.info(
            "Moved %s favorite template(s) from dashboard %s to %s",
            moved,
            old_dashboard_uuid,
            new_dashboard_uuid,
        )
    except Exception as e:
        event_id = capture_exception(e)
        logger.error(
            "Error moving favorite templates from %s to %s. Event ID: %s",
            old_dashboard_uuid,
            new_dashboard_uuid,
            event_id,
            exc_info=True,
        )
        raise


@app.task
def migrate_widgets_waba_config(
    project_uuid: str,
    old_waba_id: str,
    new_waba_id: str,
):
    """
    Update vtex_conversions widgets that store waba_id (and template_id) in
    config.filter after a WABA migration.

    Only the matching filter keys are changed; every other config field is kept.
    """
    if not old_waba_id or not new_waba_id or old_waba_id == new_waba_id:
        logger.info(
            "Skipping widget WABA config migration for project=%s "
            "(old_waba_id=%s, new_waba_id=%s)",
            project_uuid,
            old_waba_id,
            new_waba_id,
        )
        return

    try:
        project = Project.objects.get(uuid=project_uuid)
    except Project.DoesNotExist as e:
        event_id = capture_exception(e)
        logger.error(
            "Project %s not found while migrating widget WABA configs. Event ID: %s",
            project_uuid,
            event_id,
            exc_info=True,
        )
        return

    widgets = Widget.objects.filter(
        dashboard__project=project,
        source="vtex_conversions",
        config__filter__waba_id=old_waba_id,
    )

    if not widgets.exists():
        logger.info(
            "No vtex_conversions widgets with filter.waba_id=%s for project=%s",
            old_waba_id,
            project_uuid,
        )
        return

    meta_client = MetaGraphAPIClient()
    template_id_cache: dict[str, str | None] = {}
    updated_count = 0

    for widget in widgets.iterator():
        try:
            if _update_widget_waba_filter(
                widget=widget,
                old_waba_id=old_waba_id,
                new_waba_id=new_waba_id,
                meta_client=meta_client,
                template_id_cache=template_id_cache,
            ):
                updated_count += 1
        except Exception as e:
            event_id = capture_exception(e)
            logger.error(
                "Error migrating widget %s WABA config "
                "(old_waba_id=%s, new_waba_id=%s). Event ID: %s",
                widget.uuid,
                old_waba_id,
                new_waba_id,
                event_id,
                exc_info=True,
            )

    logger.info(
        "Migrated WABA config on %s widgets for project=%s "
        "(old_waba_id=%s, new_waba_id=%s)",
        updated_count,
        project_uuid,
        old_waba_id,
        new_waba_id,
    )


def _update_widget_waba_filter(
    *,
    widget: Widget,
    old_waba_id: str,
    new_waba_id: str,
    meta_client: MetaGraphAPIClient,
    template_id_cache: dict[str, str | None],
) -> bool:
    config = deepcopy(widget.config) if widget.config else {}
    filters = config.get("filter")

    if not isinstance(filters, dict):
        return False

    if filters.get("waba_id") != old_waba_id:
        return False

    filters["waba_id"] = new_waba_id

    old_template_id = filters.get("template_id")
    if old_template_id:
        if old_template_id not in template_id_cache:
            template_id_cache[old_template_id] = resolve_new_template_id(
                meta_client,
                new_waba_id=new_waba_id,
                old_template_id=str(old_template_id),
            )

        new_template_id = template_id_cache[old_template_id]
        if new_template_id:
            filters["template_id"] = new_template_id
        else:
            logger.warning(
                "Keeping original template_id=%s on widget=%s; "
                "could not resolve equivalent on new_waba_id=%s",
                old_template_id,
                widget.uuid,
                new_waba_id,
            )

    config["filter"] = filters
    widget.config = config
    widget.save(update_fields=["config"])
    return True
