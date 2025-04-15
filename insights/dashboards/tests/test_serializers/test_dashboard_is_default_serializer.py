from django.test import TestCase
from rest_framework import serializers
from insights.dashboards.models import Dashboard
from insights.dashboards.serializers import DashboardIsDefaultSerializer
from insights.projects.models import Project


class TestDashboardIsDefaultSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_default=False,
        )

    def test_set_dashboard_as_default(self):
        """
        Test that a dashboard can be set as default
        """
        serializer = DashboardIsDefaultSerializer(
            self.dashboard, data={"is_default": True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.dashboard.refresh_from_db(fields=["is_default"])
        self.assertTrue(self.dashboard.is_default)

    def test_set_dashboard_as_default_when_another_dashboard_is_default(self):
        """
        Test that a dashboard can be set as default when another dashboard,
        from the same project, is default.

        This should update the other dashboard to not be default
        and leave the dashboard from another project as it is.
        """
        another_project_dashboard = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=self.project,
            is_default=True,
        )
        dashboard_from_another_project = Dashboard.objects.create(
            name="Test Dashboard 3",
            project=Project.objects.create(name="Another Project"),
            is_default=True,
        )

        serializer = DashboardIsDefaultSerializer(
            self.dashboard, data={"is_default": True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.dashboard.refresh_from_db(fields=["is_default"])
        self.assertTrue(self.dashboard.is_default)

        another_project_dashboard.refresh_from_db(fields=["is_default"])
        self.assertFalse(another_project_dashboard.is_default)

        dashboard_from_another_project.refresh_from_db(fields=["is_default"])
        self.assertTrue(dashboard_from_another_project.is_default)

    def test_set_dashboard_as_is_default_to_false(self):
        """
        Test that a dashboard can be set as is_default to false
        """
        Dashboard.objects.filter(project=self.project, is_default=False).update(
            is_default=True
        )
        self.dashboard.refresh_from_db(fields=["is_default"])
        self.assertTrue(self.dashboard.is_default)

        serializer = DashboardIsDefaultSerializer(
            self.dashboard, data={"is_default": False}, partial=True
        )

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.assertEqual(
            context.exception.detail["is_default"][0].code,
            "cannot_set_default_dashboard_as_non_default",
        )

        self.dashboard.refresh_from_db(fields=["is_default"])
        self.assertTrue(self.dashboard.is_default)
