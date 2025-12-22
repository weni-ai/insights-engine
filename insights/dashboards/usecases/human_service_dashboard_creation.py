import copy

from django.db import transaction

from insights.dashboards.models import HUMAN_SERVICE_DASHBOARD_V2_NAME, Dashboard
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
)
from insights.widgets.models import Report, Widget


class CreateHumanService:
    def create_dashboard(self, project):
        try:
            with transaction.atomic():
                Dashboard.objects.create(
                    project=project,
                    name=HUMAN_SERVICE_DASHBOARD_V2_NAME,
                    description="Human support dashboard",
                    is_default=True,
                    grid=[],
                    is_deletable=False,
                    is_editable=False,
                )
        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")
