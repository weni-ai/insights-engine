from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.projects.models import Project
from insights.widgets.models import Report, Widget


class WidgetModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.widget = Widget.objects.create(
            name="Test Widget",
            type="chart",
            source="data_source",
            config={"config_type": "crossing_data", "filter": {}},
            dashboard=self.dashboard,
            position={"x": 1, "y": 1},
        )

    def test_is_crossing_data(self):
        self.assertTrue(self.widget.is_crossing_data)

        self.widget.config = {"config_type": "default"}
        self.assertFalse(self.widget.is_crossing_data)

    def test_str_method(self):
        self.assertEqual(str(self.widget), "Test Widget")

    def test_project_property(self):
        self.assertEqual(self.widget.project, self.dashboard.project)

    def test_is_configurable(self):
        self.dashboard.name = "Atendimento humano"
        self.assertFalse(self.widget.is_configurable)

        self.dashboard.name = "Outro Dashboard"
        self.assertTrue(self.widget.is_configurable)

    def test_source_config(self):
        filters, operation, op_field, op_sub_field, limit = self.widget.source_config()
        self.assertEqual(filters, self.widget.config.get("filter", {}))
        self.assertEqual(operation, "list")
        self.assertIsNone(op_field)
        self.assertIsNone(op_sub_field)
        self.assertIsNone(limit)

        self.widget.config = {"sub_widget_1": {"filter": {"key": "value"}}}
        filters, _, _, _, _ = self.widget.source_config(sub_widget="sub_widget_1")
        self.assertEqual(filters, {"key": "value"})

    def test_source_config_with_live_filter(self):
        self.widget.config = {"filter": {}, "live_filter": {"live_key": "live_value"}}
        filters, _, _, _, _ = self.widget.source_config(is_live=True)
        self.assertEqual(filters, {"live_key": "live_value"})


class ReportModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.widget = Widget.objects.create(
            name="Test Widget",
            type="chart",
            source="data_source",
            config={"filter": {}, "live_filter": {}},
            dashboard=self.dashboard,
            position={"x": 1, "y": 1},
        )
        self.report = Report.objects.create(
            name="Test Report",
            type="chart",
            source="data_source",
            config={"filter": {}},
            widget=self.widget,
        )

    def test_report_project_property(self):
        self.assertEqual(self.report.project, self.widget.project)

    def test_report_str_method(self):
        self.assertEqual(str(self.report), "Test Report")

    def test_report_source_config(self):
        filters, operation, op_field, op_sub_field, limit = self.report.source_config()
        self.assertEqual(filters, self.report.config.get("filter", {}))
        self.assertEqual(operation, "list")
        self.assertIsNone(op_field)
        self.assertIsNone(op_sub_field)
        self.assertIsNone(limit)

        self.report.config = {"sub_widget_1": {"filter": {"key": "value"}}}
        filters, _, _, _, _ = self.report.source_config(sub_widget="sub_widget_1")
        self.assertEqual(filters, {"key": "value"})

    def test_report_source_config_with_live_filter(self):
        self.report.config = {"filter": {}, "live_filter": {"live_key": "live_value"}}
        filters, _, _, _, _ = self.report.source_config(is_live=True)
        self.assertEqual(filters, {"live_key": "live_value"})
