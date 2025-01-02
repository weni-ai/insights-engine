from typing import TYPE_CHECKING

from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.exceptions import InvalidDashboardObject


if TYPE_CHECKING:
    from insights.projects.models import Project


class CreateTemplateMessagesDashboard:
    def create_dashboard(self, project: "Project") -> None:
        try:
            with transaction.atomic():
                template_messages_dashboard = Dashboard.objects.create(
                    project=project,
                    name="Templates de mensagens",
                    description="Dashboard de templates de mensagens do WhatsApp Business",
                    is_default=False,
                    grid=[18, 3],
                    is_deletable=False,
                    is_editable=False,
                )
                self.create_widgets(template_messages_dashboard)
        except Exception as exp:
            raise InvalidDashboardObject(f"Error creating dashboard: {exp}")

    def create_widgets(self, dashboard: Dashboard) -> None:
        pass
