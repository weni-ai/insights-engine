from unittest.mock import MagicMock

from django.core.cache import cache
from django.test import TestCase, override_settings

from insights.dashboards.models import CTWA_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.check_and_create_ctwa_dashboard import (
    CheckAndCreateCTWADashboardUseCase,
)
from insights.projects.models import Project


class TestCheckAndCreateCTWADashboardUseCase(TestCase):
    def setUp(self):
        cache.clear()
        self.project = Project.objects.create(name="Test Project")
        self.campaign_client = MagicMock()
        self.campaign_client_class = MagicMock(return_value=self.campaign_client)
        self.usecase = CheckAndCreateCTWADashboardUseCase(
            campaign_client_class=self.campaign_client_class,
        )

    def test_creates_dashboard_when_project_has_campaigns(self):
        self.campaign_client.list_campaigns.return_value = {
            "count": 1,
            "results": [{"name": "Black friday", "uuid": "abc"}],
        }

        created = self.usecase.execute(self.project.uuid)

        self.assertTrue(created)
        self.assertTrue(
            Dashboard.objects.filter(
                project=self.project, name=CTWA_DASHBOARD_NAME
            ).exists()
        )

    def test_does_not_create_dashboard_when_project_has_no_campaigns(self):
        self.campaign_client.list_campaigns.return_value = {
            "count": 0,
            "results": [],
        }

        created = self.usecase.execute(self.project.uuid)

        self.assertFalse(created)
        self.assertFalse(
            Dashboard.objects.filter(
                project=self.project, name=CTWA_DASHBOARD_NAME
            ).exists()
        )

    def test_skips_flows_when_dashboard_already_exists(self):
        Dashboard.objects.create(
            project=self.project,
            name=CTWA_DASHBOARD_NAME,
            description="Click to WhatsApp dashboard",
        )

        created = self.usecase.execute(self.project.uuid)

        self.assertTrue(created)
        self.campaign_client.list_campaigns.assert_not_called()

    @override_settings(CTWA_DASHBOARD_CHECK_COOLDOWN_TTL=900)
    def test_respects_cooldown_and_does_not_call_flows_twice(self):
        self.campaign_client.list_campaigns.return_value = {
            "count": 0,
            "results": [],
        }

        self.usecase.execute(self.project.uuid)
        self.usecase.execute(self.project.uuid)

        self.campaign_client.list_campaigns.assert_called_once()

    def test_does_not_set_cooldown_when_flows_raises(self):
        self.campaign_client.list_campaigns.side_effect = Exception("flows down")

        created = self.usecase.execute(self.project.uuid)

        self.assertFalse(created)
        self.assertIsNone(
            cache.get(self.usecase._get_cache_key(self.project.uuid))
        )
