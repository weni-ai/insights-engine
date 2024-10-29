import pytest
from django.test import TestCase
from insights.dashboards.models import Dashboard
from insights.widgets.models import Widget, Report
from insights.projects.models import Project


class WidgetModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project"
        )  # Ajuste o modelo Project conforme necessário
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,  # Garantir que o project seja definido
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
        # Linha 22: Teste do método is_crossing_data
        self.assertTrue(self.widget.is_crossing_data)

        # Testando quando não é "crossing_data"
        self.widget.config = {"config_type": "default"}
        self.assertFalse(self.widget.is_crossing_data)

    def test_str_method(self):
        # Linha 32: Teste do método __str__
        self.assertEqual(str(self.widget), "Test Widget")

    def test_project_property(self):
        # Linha 36: Teste da propriedade project
        self.assertEqual(self.widget.project, self.dashboard.project)

    def test_is_configurable(self):
        # Linha 40: Teste da propriedade is_configurable
        self.dashboard.name = "Atendimento humano"
        self.assertFalse(self.widget.is_configurable)

        # Teste com outro nome de dashboard
        self.dashboard.name = "Outro Dashboard"
        self.assertTrue(self.widget.is_configurable)

    def test_source_config(self):
        # Linhas 43-48: Teste do método source_config
        filters, operation, op_field, op_sub_field, limit = self.widget.source_config()
        self.assertEqual(filters, self.widget.config.get("filter", {}))
        self.assertEqual(operation, "list")
        self.assertIsNone(op_field)
        self.assertIsNone(op_sub_field)
        self.assertIsNone(limit)

        # Testando com sub_widget
        self.widget.config = {"sub_widget_1": {"filter": {"key": "value"}}}
        filters, _, _, _, _ = self.widget.source_config(sub_widget="sub_widget_1")
        self.assertEqual(filters, {"key": "value"})

    def test_source_config_with_live_filter(self):
        # Teste do método source_config com live_filter
        self.widget.config = {"filter": {}, "live_filter": {"live_key": "live_value"}}
        filters, _, _, _, _ = self.widget.source_config(is_live=True)
        self.assertEqual(filters, {"live_key": "live_value"})


class ReportModelTest(TestCase):
    def setUp(self):
        # Setup inicial para o modelo Report
        self.project = Project.objects.create(
            name="Test Project"
        )  # Ajuste o modelo Project conforme necessário
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,  # Garantir que o project seja definido
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
        # Linha 64: Teste da propriedade project no Report
        self.assertEqual(self.report.project, self.widget.project)

    def test_report_str_method(self):
        # Linha 67: Teste do método __str__ no Report
        self.assertEqual(str(self.report), "Test Report")

    def test_report_source_config(self):
        # Linhas 70-75: Teste do método source_config no Report
        filters, operation, op_field, op_sub_field, limit = self.report.source_config()
        self.assertEqual(filters, self.report.config.get("filter", {}))
        self.assertEqual(operation, "list")
        self.assertIsNone(op_field)
        self.assertIsNone(op_sub_field)
        self.assertIsNone(limit)

        # Testando com sub_widget no Report
        self.report.config = {"sub_widget_1": {"filter": {"key": "value"}}}
        filters, _, _, _, _ = self.report.source_config(sub_widget="sub_widget_1")
        self.assertEqual(filters, {"key": "value"})

    def test_report_source_config_with_live_filter(self):
        # Testando com live_filter no Report
        self.report.config = {"filter": {}, "live_filter": {"live_key": "live_value"}}
        filters, _, _, _, _ = self.report.source_config(is_live=True)
        self.assertEqual(filters, {"live_key": "live_value"})
