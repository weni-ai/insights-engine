from django.db import transaction

from insights.dashboards.models import CTWA_DASHBOARD_NAME, Dashboard


class CreateCTWADashboard:
    @transaction.atomic
    def create_dashboard(self, project):
        dashboard, _created = Dashboard.objects.get_or_create(
            project=project,
            name=CTWA_DASHBOARD_NAME,
            defaults={
                "description": "Click to WhatsApp dashboard",
                "is_default": False,
                "grid": [0, 0],
                "is_deletable": False,
                "is_editable": False,
                "config": {
                    "type": "ctwa",
                },
            },
        )
        return dashboard
