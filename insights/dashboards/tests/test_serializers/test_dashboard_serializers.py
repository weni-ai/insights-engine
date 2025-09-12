from django.conf import settings
from django.test import TestCase
from rest_framework import serializers
from insights.dashboards.models import Dashboard
from insights.dashboards.serializers import (
    DashboardEditSerializer,
    DashboardIsDefaultSerializer,
    DashboardReportSerializer,
    DashboardSerializer,
    DashboardWidgetsSerializer,
)
from insights.projects.models import Project
from insights.widgets.models import Report, Widget


class TestDashboardSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_default=False,
            grid={},
            is_deletable=True,
            is_editable=True,
            config={},
        )

    def test_serialization(self):
        serializer = DashboardSerializer(instance=self.dashboard)
        data = serializer.data
        self.assertEqual(data["name"], self.dashboard.name)
        self.assertEqual(data["is_default"], self.dashboard.is_default)
        self.assertEqual(data["uuid"], str(self.dashboard.uuid))

    def test_add_whatsapp_integration_in_dashboard_config(self):
        data = {
            "name": "Test Dashboard",
            "config": {"is_whatsapp_integration": True, "waba_id": "123"},
        }
        serializer = DashboardSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["config"][0].code, "whatsapp_integration_cannot_be_added"
        )


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

    def test_set_dashboard_as_default_to_the_same_value_of_false(self):
        """
        Test that nothing happens when a dashboard is set as is_default to False
        and it is already False. This should cover the return self.instance line.
        """
        serializer = DashboardIsDefaultSerializer(
            self.dashboard, data={"is_default": False}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        saved_instance = serializer.save()

        self.dashboard.refresh_from_db(fields=["is_default"])
        self.assertFalse(self.dashboard.is_default)
        self.assertIs(saved_instance, self.dashboard)


class TestDashboardReportSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.widget = Widget.objects.create(
            dashboard=self.dashboard,
            position={},
            config={},
            source="test_source",
            type="test_type",
        )

    def test_get_url_with_external_url_in_dict_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config={"external_url": "http://example.com"},
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["url"], "http://example.com")

    def test_get_url_without_external_url_in_dict_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config={"other_key": "value"},
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        expected_url = f"{settings.INSIGHTS_DOMAIN}/v1/dashboards/{self.dashboard.uuid}/widgets/{self.widget.uuid}/report/"
        self.assertEqual(serializer.data["url"], expected_url)

    def test_get_url_with_external_url_in_list_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config=[{"external_url": "http://example.com"}],
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["url"], "http://example.com")

    def test_get_url_without_external_url_in_list_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config=[{"other_key": "value"}],
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        expected_url = f"{settings.INSIGHTS_DOMAIN}/v1/dashboards/{self.dashboard.uuid}/widgets/{self.widget.uuid}/report/"
        self.assertEqual(serializer.data["url"], expected_url)

    def test_get_type_with_external_url_in_dict_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config={"external_url": "http://example.com"},
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["type"], "external")

    def test_get_type_without_external_url_in_dict_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config={"other_key": "value"},
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["type"], "internal")

    def test_get_type_with_external_url_in_list_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config=[{"external_url": "http://example.com"}],
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["type"], "external")

    def test_get_type_without_external_url_in_list_config(self):
        report = Report.objects.create(
            widget=self.widget,
            config=[{"other_key": "value"}],
            source="test_source",
            type="test_type",
        )
        serializer = DashboardReportSerializer(instance=report)
        self.assertEqual(serializer.data["type"], "internal")


class TestDashboardWidgetsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(project=self.project)
        self.widget = Widget.objects.create(
            dashboard=self.dashboard,
            position={},
            config={},
            source="test_source",
            type="test_type",
        )
        self.report = Report.objects.create(
            widget=self.widget,
            config={"external_url": "http://test.com"},
            source="test_source",
            type="test_type",
        )

    def test_serialization(self):
        serializer = DashboardWidgetsSerializer(instance=self.widget)
        data = serializer.data
        self.assertTrue(data["is_configurable"])
        self.assertIn("report", data)
        self.assertEqual(data["report"]["url"], "http://test.com")
        self.assertEqual(data["report"]["type"], "external")


class TestDashboardEditSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )

    def test_edit_dashboard(self):
        data = {"name": "New Name", "config": {"new": "config"}}
        serializer = DashboardEditSerializer(instance=self.dashboard, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.name, "New Name")
        self.assertEqual(self.dashboard.config, {"new": "config"})

    def test_edit_dashboard_with_whatsapp_integration(self):
        data = {
            "name": "New Name",
            "config": {"is_whatsapp_integration": True, "waba_id": "123"},
        }
        serializer = DashboardEditSerializer(instance=self.dashboard, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["config"][0].code, "whatsapp_integration_cannot_be_edited"
        )
