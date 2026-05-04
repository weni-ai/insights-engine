from typing import Optional
from uuid import UUID
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.projects.models import Project
from insights.widgets.models import Widget


class CheckProjectSalesFunnelDataUseCase:
    """
    Usecase to check if sales funnel data exists for a project.
    """

    WIDGET_NAME = "conversations_dashboard.sales_funnel_widget.title"
    WIDGET_TYPE = "sales_funnel"
    WIDGET_SOURCE = "conversations.sales_funnel"

    def __init__(self, datalake_service: BaseDatalakeConversationsMetricsService):
        self.datalake_service = datalake_service

    def _check_dashboard_config(self, dashboard: Dashboard) -> bool:
        """
        Check if sales funnel data exists for a dashboard.
        """
        config: dict = dashboard.config or {}
        sales_funnel_config: Optional[dict] = config.get("sales_funnel", {})
        sales_funnel_has_data: bool = sales_funnel_config.get("has_data", False)

        return sales_funnel_has_data

    def _update_dashboard_config(self, dashboard: Dashboard) -> None:
        """
        Update dashboard config.
        """
        config: dict = dashboard.config or {}
        sales_funnel_config: Optional[dict] = config.get("sales_funnel", {})
        sales_funnel_config["has_data"] = True
        dashboard.config = config
        dashboard.save(update_fields=["config"])

    def _check_if_widget_exists(self, dashboard: Dashboard) -> bool:
        """
        Check if widget exists.
        """
        return Widget.objects.filter(
            dashboard=dashboard,
            name=self.WIDGET_NAME,
            type=self.WIDGET_TYPE,
            source=self.WIDGET_SOURCE,
        ).exists()

    def _create_sales_funnel_widget(self, dashboard: Dashboard) -> Widget:
        """
        Create sales funnel widget.
        """
        return Widget.objects.create(
            dashboard=dashboard,
            name=self.WIDGET_NAME,
            type=self.WIDGET_TYPE,
            source=self.WIDGET_SOURCE,
            config={},
            position={},
        )

    def execute(self, project_uuid: UUID) -> bool:
        """
        Check if sales funnel data exists for a project.
        """
        # TODO: Add cooldown to avoid excessive calls to the datalake.

        if not (
            conversations_dashboard := Dashboard.objects.filter(
                project_id=project_uuid, name=CONVERSATIONS_DASHBOARD_NAME
            ).first()
        ):
            return False

        if self._check_dashboard_config(conversations_dashboard):
            return True

        exists_on_datalake = self.datalake_service.check_if_sales_funnel_data_exists(
            project_uuid
        )

        if not exists_on_datalake:
            return False

        self._update_dashboard_config(conversations_dashboard)

        if not self._check_if_widget_exists(conversations_dashboard):
            self._create_sales_funnel_widget(conversations_dashboard)

        return True
