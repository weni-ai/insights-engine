from django.test import TestCase

from insights.dashboards.models import CTWA_DASHBOARD_NAME, Dashboard
from insights.dashboards.usecases.ctwa_dashboard_creation import CreateCTWADashboard
from insights.projects.models import Project


class TestCreateCTWADashboard(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.usecase = CreateCTWADashboard()

    def test_create_dashboard_persists_dashboard_with_expected_fields(self):
        dashboard = self.usecase.create_dashboard(self.project)

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(dashboard.project, self.project)
        self.assertEqual(dashboard.name, CTWA_DASHBOARD_NAME)
        self.assertEqual(dashboard.description, "Click to WhatsApp dashboard")
        self.assertFalse(dashboard.is_default)
        self.assertFalse(dashboard.is_deletable)
        self.assertFalse(dashboard.is_editable)
        self.assertEqual(dashboard.grid, [0, 0])
        self.assertEqual(dashboard.config, {"type": "ctwa"})

    def test_create_dashboard_is_idempotent(self):
        first = self.usecase.create_dashboard(self.project)
        second = self.usecase.create_dashboard(self.project)

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(first.uuid, second.uuid)
