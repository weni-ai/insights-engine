import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from sentry_sdk import capture_exception

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
    DatalakeConversationsMetricsService,
)
from insights.widgets.models import Widget


logger = logging.getLogger(__name__)


class ShouldShowConversationsDashboardMockUseCase:
    """
    Decide whether the conversational dashboard should be shown with mock data.

    Returns True only when the project has no conversation_classification events
    and no conversational widget with a valid config.
    """

    CACHE_KEY_PREFIX = "conversations_dashboard_should_show_mock"

    def __init__(
        self,
        datalake_service: BaseDatalakeConversationsMetricsService | None = None,
    ):
        self.datalake_service = (
            datalake_service or DatalakeConversationsMetricsService()
        )

    def _get_cache_key(self, project_uuid: UUID) -> str:
        return f"{self.CACHE_KEY_PREFIX}:{project_uuid}"

    @classmethod
    def invalidate(cls, project_uuid: UUID) -> None:
        cache.delete(f"{cls.CACHE_KEY_PREFIX}:{project_uuid}")

    def _cache_result(self, project_uuid: UUID, should_show_mock: bool) -> bool:
        timeout = (
            settings.CONVERSATIONS_DASHBOARD_MOCK_CHECK_NEGATIVE_TTL
            if should_show_mock
            else settings.CONVERSATIONS_DASHBOARD_MOCK_CHECK_POSITIVE_TTL
        )
        cache.set(self._get_cache_key(project_uuid), should_show_mock, timeout=timeout)
        return should_show_mock

    def _has_persisted_events(self, dashboard: Dashboard) -> bool:
        config = dashboard.config or {}
        conversations_data = config.get("conversations_data") or {}
        return bool(conversations_data.get("has_events"))

    def _persist_has_events(self, dashboard: Dashboard) -> None:
        config = dict(dashboard.config or {})
        conversations_data = dict(config.get("conversations_data") or {})
        conversations_data["has_events"] = True
        config["conversations_data"] = conversations_data
        dashboard.config = config
        dashboard.save(update_fields=["config"])

    def _has_configured_widgets(self, dashboard: Dashboard) -> bool:
        config = dashboard.config or {}
        sales_funnel_config = config.get("sales_funnel") or {}
        if sales_funnel_config.get("has_data"):
            return True

        csat_nps_ai = Q(
            source__in=["conversations.csat", "conversations.nps"],
            config__datalake_config__agent_uuid__gt="",
        )
        csat_nps_human = Q(
            source__in=["conversations.csat", "conversations.nps"],
            config__type="flow_result",
            config__filter__flow__gt="",
            config__op_field__gt="",
        )
        custom = Q(source="conversations.custom")
        crosstab = Q(source="conversations.crosstab")
        absolute_numbers = Q(
            source="conversations.absolute_numbers.child",
            config__operation__gt="",
            config__key__gt="",
            config__agent_uuid__gt="",
        )

        return (
            Widget.objects.filter(
                Q(dashboard=dashboard) | Q(parent__dashboard=dashboard)
            )
            .filter(
                csat_nps_ai | csat_nps_human | custom | crosstab | absolute_numbers
            )
            .exists()
        )

    def execute(self, project_uuid: UUID) -> bool:
        cache_key = self._get_cache_key(project_uuid)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        dashboard = Dashboard.objects.filter(
            project_id=project_uuid, name=CONVERSATIONS_DASHBOARD_NAME
        ).first()

        if not dashboard:
            return self._cache_result(project_uuid, True)

        if self._has_persisted_events(dashboard):
            return self._cache_result(project_uuid, False)

        executor = ThreadPoolExecutor(max_workers=1)
        wait_for_events = True
        try:
            events_future = executor.submit(
                self.datalake_service.check_if_conversation_classification_data_exists,
                project_uuid,
            )

            if self._has_configured_widgets(dashboard):
                wait_for_events = False
                return self._cache_result(project_uuid, False)

            try:
                has_events = events_future.result()
            except Exception as e:
                logger.error(
                    "[SHOULD SHOW DASHBOARD MOCK] Failed to check "
                    "conversation classification events for project %s: %s",
                    project_uuid,
                    e,
                    exc_info=True,
                )
                capture_exception(e)
                return True

            if has_events:
                self._persist_has_events(dashboard)
                return self._cache_result(project_uuid, False)

            return self._cache_result(project_uuid, True)
        finally:
            executor.shutdown(wait=wait_for_events)
