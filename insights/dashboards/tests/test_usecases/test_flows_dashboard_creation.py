from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.flows_dashboard_creation import (
    CreateFlowsDashboard,
)
from insights.projects.models import Project
from insights.projects.usecases.dashboard_dto import FlowsDashboardCreationDTO
from insights.widgets.models import Widget


class TestCreateFlowsDashboard(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def test_create_dashboard_with_funnel_amount_3(self):
        params = FlowsDashboardCreationDTO(
            project=self.project,
            dashboard_name="Test Dashboard",
            funnel_amount=3,
            currency_type="BRL",
        )
        created_dashboard = CreateFlowsDashboard(params).create_dashboard()

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(Widget.objects.filter(dashboard=created_dashboard).count(), 3)
        self.assertEqual(
            Widget.objects.filter(
                dashboard=created_dashboard, type="empty_column"
            ).count(),
            3,
        )
        self.assertEqual(created_dashboard.config["currency_type"], "BRL")

    def test_create_dashboard_with_funnel_amount_2(self):
        params = FlowsDashboardCreationDTO(
            project=self.project,
            dashboard_name="Test Dashboard",
            funnel_amount=2,
            currency_type="USD",
        )
        created_dashboard = CreateFlowsDashboard(params).create_dashboard()

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(Widget.objects.filter(dashboard=created_dashboard).count(), 5)
        self.assertEqual(
            Widget.objects.filter(
                dashboard=created_dashboard, type="empty_column"
            ).count(),
            2,
        )
        self.assertEqual(
            Widget.objects.filter(dashboard=created_dashboard, type="card").count(),
            3,
        )
        self.assertEqual(created_dashboard.config["currency_type"], "USD")

    def test_create_dashboard_with_funnel_amount_1(self):
        params = FlowsDashboardCreationDTO(
            project=self.project,
            dashboard_name="Test Dashboard",
            funnel_amount=1,
            currency_type="EUR",
        )
        created_dashboard = CreateFlowsDashboard(params).create_dashboard()

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(Widget.objects.filter(dashboard=created_dashboard).count(), 7)
        self.assertEqual(
            Widget.objects.filter(
                dashboard=created_dashboard, type="empty_column"
            ).count(),
            1,
        )
        self.assertEqual(
            Widget.objects.filter(dashboard=created_dashboard, type="card").count(),
            6,
        )
        self.assertEqual(created_dashboard.config["currency_type"], "EUR")

    def test_create_dashboard_with_default_funnel_amount(self):
        params = FlowsDashboardCreationDTO(
            project=self.project,
            dashboard_name="Test Dashboard",
            funnel_amount=0,
            currency_type="BRL",
        )
        created_dashboard = CreateFlowsDashboard(params).create_dashboard()

        self.assertEqual(Dashboard.objects.count(), 1)
        self.assertEqual(Widget.objects.filter(dashboard=created_dashboard).count(), 9)
        self.assertEqual(
            Widget.objects.filter(dashboard=created_dashboard, type="card").count(),
            9,
        )
        self.assertEqual(created_dashboard.config["currency_type"], "BRL")
