import logging
from uuid import UUID

from django.conf import settings
from django.core.cache import cache

from insights.dashboards.models import CTWA_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.ctwa_dashboard_creation import CreateCTWADashboard
from insights.projects.models import Project
from insights.sources.meta.campaign.clients import FlowsCampaignClient

logger = logging.getLogger(__name__)


class CheckAndCreateCTWADashboardUseCase:
    CACHE_KEY_PREFIX = "ctwa_dashboard_check"

    def __init__(
        self,
        campaign_client_class=FlowsCampaignClient,
        create_dashboard=None,
    ):
        self.campaign_client_class = campaign_client_class
        self.create_dashboard = create_dashboard or CreateCTWADashboard()

    def _get_cache_key(self, project_uuid: UUID | str) -> str:
        return f"{self.CACHE_KEY_PREFIX}:{project_uuid}"

    def _has_campaigns(self, project_uuid: str) -> bool:
        campaigns = self.campaign_client_class(project_uuid).list_campaigns(
            limit=1,
            offset=0,
        )
        if campaigns.get("count"):
            return True
        return bool(campaigns.get("results"))

    def execute(self, project_uuid: UUID | str) -> bool:
        project = Project.objects.filter(uuid=project_uuid).first()
        if not project:
            logger.warning(
                "[ CheckAndCreateCTWADashboardUseCase ] Project %s not found",
                project_uuid,
            )
            return False

        if Dashboard.objects.filter(
            project=project, name=CTWA_DASHBOARD_NAME
        ).exists():
            return True

        cache_key = self._get_cache_key(project_uuid)
        if cache.get(cache_key) is not None:
            return False

        try:
            has_campaigns = self._has_campaigns(str(project.uuid))
        except Exception:
            logger.exception(
                "[ CheckAndCreateCTWADashboardUseCase ] Error listing campaigns for project %s",
                project.uuid,
            )
            return False

        cache.set(
            cache_key,
            has_campaigns,
            timeout=settings.CTWA_DASHBOARD_CHECK_COOLDOWN_TTL,
        )

        if not has_campaigns:
            return False

        self.create_dashboard.create_dashboard(project)
        return True
