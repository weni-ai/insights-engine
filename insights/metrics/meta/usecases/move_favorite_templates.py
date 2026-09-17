from __future__ import annotations

import logging
from uuid import UUID

from insights.dashboards.models import Dashboard
from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.models import (
    FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD,
    FavoriteTemplate,
)
from insights.metrics.meta.usecases.waba_migration_analytics import (
    find_exact_template_id_by_name,
)

logger = logging.getLogger(__name__)


class MoveFavoriteTemplatesUseCase:
    """
    Copy favorite templates from a soft-deleted dashboard to the new one after
    a WABA migration, resolving each template id on the new WABA by exact name.
    """

    def __init__(self, meta_client=None):
        self.meta_client = meta_client or MetaGraphAPIClient()

    def execute(
        self,
        *,
        old_dashboard_uuid: UUID | str,
        new_dashboard_uuid: UUID | str,
    ) -> int:
        try:
            old_dashboard = Dashboard.all_objects.get(uuid=old_dashboard_uuid)
        except Dashboard.DoesNotExist:
            logger.info(
                "Old dashboard %s not found when moving favorite templates",
                old_dashboard_uuid,
            )
            return 0

        try:
            new_dashboard = Dashboard.objects.get(uuid=new_dashboard_uuid)
        except Dashboard.DoesNotExist:
            logger.info(
                "New dashboard %s not found when moving favorite templates",
                new_dashboard_uuid,
            )
            return 0

        new_waba_id = (new_dashboard.config or {}).get("waba_id")
        if not new_waba_id:
            logger.info(
                "New dashboard %s has no waba_id; skipping favorite templates move",
                new_dashboard_uuid,
            )
            return 0

        favorites = list(FavoriteTemplate.objects.filter(dashboard=old_dashboard))
        if not favorites:
            return 0

        moved = 0
        for favorite in favorites:
            if (
                FavoriteTemplate.objects.filter(dashboard=new_dashboard).count()
                >= FAVORITE_TEMPLATE_LIMIT_PER_DASHBOARD
            ):
                logger.info(
                    "Favorite template limit reached on dashboard %s; "
                    "stopping favorite templates move",
                    new_dashboard_uuid,
                )
                break

            new_template_id = self._resolve_template_id_on_waba(
                waba_id=new_waba_id,
                template_name=favorite.name,
            )
            if not new_template_id:
                logger.info(
                    "No exact template name match for name=%s on new_waba_id=%s; "
                    "skipping favorite from old dashboard %s",
                    favorite.name,
                    new_waba_id,
                    old_dashboard_uuid,
                )
                continue

            _, created = FavoriteTemplate.objects.get_or_create(
                dashboard=new_dashboard,
                template_id=new_template_id,
                defaults={"name": favorite.name},
            )
            if created:
                moved += 1

        return moved

    def _resolve_template_id_on_waba(
        self, *, waba_id: str, template_name: str
    ) -> str | None:
        if not template_name:
            return None

        templates_response = self.meta_client.get_templates_list(
            waba_id=waba_id,
            name=template_name,
        )
        return find_exact_template_id_by_name(templates_response, template_name)
