from typing import Optional
from uuid import UUID

from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard


class CheckProjectSalesFunnelOnDashboardUseCase:
    """
    Usecase to check if sales funnel data exists for a project
    by looking at the dashboard config only (no datalake call).
    """

    def _check_dashboard_config(self, dashboard: Dashboard) -> bool:
        config: dict = dashboard.config or {}
        sales_funnel_config: Optional[dict] = config.get("sales_funnel", {})
        return sales_funnel_config.get("has_data", False)

    def execute(self, project_uuid: UUID) -> bool:
        conversations_dashboard = Dashboard.objects.filter(
            project_id=project_uuid, name=CONVERSATIONS_DASHBOARD_NAME
        ).first()

        if not conversations_dashboard:
            return False

        return self._check_dashboard_config(conversations_dashboard)
