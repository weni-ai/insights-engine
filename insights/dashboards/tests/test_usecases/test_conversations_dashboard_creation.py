from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.conversations_dashboard_creation import (
    ConversationsDashboardCreation,
)
from insights.projects.models import Project


class TestConversationsDashboardCreation(TestCase):
    def setUp(self):
        self.usecase = ConversationsDashboardCreation()

        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_create_for_project_when_dashboard_does_not_exist(self):
        self.assertIsNone(self.usecase.get_for_project(self.project))

        dashboard = self.usecase.create_for_project(self.project)

        self.assertIsInstance(dashboard, Dashboard)
        self.assertEqual(dashboard.name, "weni_conversations_dashboard")
        self.assertEqual(dashboard.project, self.project)
        self.assertEqual(dashboard.is_deletable, False)
        self.assertEqual(dashboard.is_editable, False)
        self.assertEqual(dashboard.grid, [])

    def test_create_for_project_when_dashboard_does_exist(self):
        existing_dashboard = self.usecase.create_for_project(self.project)

        dashboard = self.usecase.create_for_project(self.project)

        self.assertEqual(dashboard, existing_dashboard)

    def test_get_for_project_when_dashboard_does_not_exist(self):
        self.assertIsNone(self.usecase.get_for_project(self.project))

    def test_get_for_project_when_dashboard_does_exist(self):
        existing_dashboard = self.usecase.create_for_project(self.project)

        dashboard = self.usecase.get_for_project(self.project)

        self.assertEqual(dashboard, existing_dashboard)

    def test_create_for_all_projects_when_dashboard_does_not_exist(self):
        for i in range(4):
            Project.objects.create(
                name=f"Test Project {i}",
            )

        created = self.usecase.create_for_all_projects(bulk_size=2)

        self.assertEqual(created, Project.objects.count())

        self.assertEqual(
            Dashboard.objects.filter(name="weni_conversations_dashboard").count(),
            Project.objects.count(),
        )

    def test_create_for_all_projects_when_dashboard_does_exist_for_some_projects(self):
        self.usecase.create_for_project(self.project)

        for i in range(3):
            Project.objects.create(
                name=f"Test Project {i}",
            )

        self.assertEqual(
            Dashboard.objects.filter(name="weni_conversations_dashboard").count(),
            1,
        )

        created = self.usecase.create_for_all_projects(bulk_size=2)

        self.assertEqual(created, Project.objects.exclude(pk=self.project.pk).count())

        self.assertEqual(
            Dashboard.objects.filter(name="weni_conversations_dashboard").count(),
            Project.objects.all().count(),
        )
