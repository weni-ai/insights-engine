from typing import Optional
from uuid import UUID

from django.conf import settings
from django.core.cache import cache

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.widgets.models import Widget


class CheckProjectSalesFunnelOnDatalakeUseCase:
    """
    Usecase to check if sales funnel data exists on the datalake,
    then update the dashboard config and create the widget if needed.
    """

    WIDGET_NAME = "conversations_dashboard.sales_funnel_widget.title"
    WIDGET_TYPE = "sales_funnel"
    WIDGET_SOURCE = "conversations.sales_funnel"
    CACHE_KEY_PREFIX = "sales_funnel_check"

    def __init__(self, datalake_service: BaseDatalakeConversationsMetricsService):
        self.datalake_service = datalake_service

    def _check_dashboard_config(self, dashboard: Dashboard) -> bool:
        config: dict = dashboard.config or {}
        sales_funnel_config: Optional[dict] = config.get("sales_funnel", {})
        return sales_funnel_config.get("has_data", False)

    def _update_dashboard_config(self, dashboard: Dashboard) -> None:
        config: dict = dashboard.config or {}
        sales_funnel_config: Optional[dict] = config.get("sales_funnel", {})
        sales_funnel_config["has_data"] = True
        dashboard.config = config
        dashboard.save(update_fields=["config"])

    def _check_if_widget_exists(self, dashboard: Dashboard) -> bool:
        return Widget.objects.filter(
            dashboard=dashboard,
            name=self.WIDGET_NAME,
            type=self.WIDGET_TYPE,
            source=self.WIDGET_SOURCE,
        ).exists()

    def _create_sales_funnel_widget(self, dashboard: Dashboard) -> Widget:
        return Widget.objects.create(
            dashboard=dashboard,
            name=self.WIDGET_NAME,
            type=self.WIDGET_TYPE,
            source=self.WIDGET_SOURCE,
            config={},
            position={},
        )

    def _get_cache_key(self, project_uuid: UUID) -> str:
        return f"{self.CACHE_KEY_PREFIX}:{project_uuid}"

    def execute(self, project_uuid: UUID) -> bool:
        conversations_dashboard = Dashboard.objects.filter(
            project_id=project_uuid, name=CONVERSATIONS_DASHBOARD_NAME
        ).first()

        if not conversations_dashboard:
            return False

        if self._check_dashboard_config(conversations_dashboard):
            return True

        cache_key = self._get_cache_key(project_uuid)

        if cached_exists_on_datalake := cache.get(cache_key):
            return cached_exists_on_datalake

        exists_on_datalake = self.datalake_service.check_if_sales_funnel_data_exists(
            project_uuid
        )

        cache.set(
            cache_key,
            exists_on_datalake,
            timeout=settings.SALES_FUNNEL_CHECK_COOLDOWN_TTL,
        )

        if not exists_on_datalake:
            return False

        self._update_dashboard_config(conversations_dashboard)

        if not self._check_if_widget_exists(conversations_dashboard):
            self._create_sales_funnel_widget(conversations_dashboard)

        return True
