from uuid import uuid4
from django.test import TestCase

from insights.projects.models import Project
from insights.dashboards.models import Dashboard
from insights.widgets.models import Widget
from insights.metrics.conversations.reports.available_widgets import (
    get_csat_ai_widget,
    get_csat_human_widget,
    get_nps_ai_widget,
    get_nps_human_widget,
    get_custom_widgets,
)


class TestAvailableWidgets(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name="Test Dashboard",
            description="Test Dashboard Description",
        )

    def test_get_csat_ai_widget_with_valid_widget(self):
        """Test get_csat_ai_widget returns widget when valid CSAT AI widget exists"""
        agent_uuid = uuid4()
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT AI Widget",
            type="chart",
            source="conversations.csat",
            config={"datalake_config": {"type": "CSAT", "agent_uuid": str(agent_uuid)}},
            position={},
        )

        result = get_csat_ai_widget(self.project)

        self.assertEqual(result, widget)
        self.assertEqual(result.source, "conversations.csat")
        self.assertEqual(result.config["datalake_config"]["type"], "CSAT")
        self.assertEqual(
            result.config["datalake_config"]["agent_uuid"], str(agent_uuid)
        )

    def test_get_csat_ai_widget_without_widget(self):
        """Test get_csat_ai_widget returns None when no CSAT AI widget exists"""
        result = get_csat_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_ai_widget_without_agent_uuid(self):
        """Test get_csat_ai_widget returns None when widget exists but has no agent_uuid"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT AI Widget",
            type="chart",
            source="conversations.csat",
            config={
                "datalake_config": {
                    "type": "CSAT"
                    # Missing agent_uuid
                }
            },
            position={},
        )

        result = get_csat_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_ai_widget_with_different_source(self):
        """Test get_csat_ai_widget returns None when widget has different source"""
        agent_uuid = uuid4()
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS AI Widget",
            type="chart",
            source="conversations.nps",  # Different source
            config={"datalake_config": {"type": "CSAT", "agent_uuid": str(agent_uuid)}},
            position={},
        )

        result = get_csat_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_ai_widget_with_different_type(self):
        """Test get_csat_ai_widget returns None when widget has different type"""
        agent_uuid = uuid4()
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT AI Widget",
            type="chart",
            source="conversations.csat",
            config={
                "datalake_config": {
                    "type": "NPS",  # Different type
                    "agent_uuid": str(agent_uuid),
                }
            },
            position={},
        )

        result = get_csat_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_nps_ai_widget_with_valid_widget(self):
        """Test get_nps_ai_widget returns widget when valid NPS AI widget exists"""
        agent_uuid = uuid4()
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS AI Widget",
            type="chart",
            source="conversations.nps",
            config={"datalake_config": {"type": "NPS", "agent_uuid": str(agent_uuid)}},
            position={},
        )

        result = get_nps_ai_widget(self.project)

        self.assertEqual(result, widget)
        self.assertEqual(result.source, "conversations.nps")
        self.assertEqual(result.config["datalake_config"]["type"], "NPS")
        self.assertEqual(
            result.config["datalake_config"]["agent_uuid"], str(agent_uuid)
        )

    def test_get_nps_ai_widget_without_widget(self):
        """Test get_nps_ai_widget returns None when no NPS AI widget exists"""
        result = get_nps_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_nps_ai_widget_without_agent_uuid(self):
        """Test get_nps_ai_widget returns None when widget exists but has no agent_uuid"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS AI Widget",
            type="chart",
            source="conversations.nps",
            config={
                "datalake_config": {
                    "type": "NPS"
                    # Missing agent_uuid
                }
            },
            position={},
        )

        result = get_nps_ai_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_human_widget_with_valid_widget(self):
        """Test get_csat_human_widget returns widget when valid CSAT human widget exists"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Human Widget",
            type="chart",
            source="conversations.csat",
            config={
                "type": "flow_result",
                "filter": {"flow": "csat_flow"},
                "op_field": "satisfaction_score",
            },
            position={},
        )

        result = get_csat_human_widget(self.project)

        self.assertEqual(result, widget)
        self.assertEqual(result.source, "conversations.csat")
        self.assertEqual(result.config["type"], "flow_result")
        self.assertEqual(result.config["filter"]["flow"], "csat_flow")
        self.assertEqual(result.config["op_field"], "satisfaction_score")

    def test_get_csat_human_widget_without_widget(self):
        """Test get_csat_human_widget returns None when no CSAT human widget exists"""
        result = get_csat_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_human_widget_without_flow(self):
        """Test get_csat_human_widget returns None when widget exists but has no flow"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Human Widget",
            type="chart",
            source="conversations.csat",
            config={
                "type": "flow_result",
                "filter": {
                    # Missing flow
                },
                "op_field": "satisfaction_score",
            },
            position={},
        )

        result = get_csat_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_human_widget_without_op_field(self):
        """Test get_csat_human_widget returns None when widget exists but has no op_field"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Human Widget",
            type="chart",
            source="conversations.csat",
            config={
                "type": "flow_result",
                "filter": {"flow": "csat_flow"},
                # Missing op_field
            },
            position={},
        )

        result = get_csat_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_csat_human_widget_with_different_type(self):
        """Test get_csat_human_widget returns None when widget has different type"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Human Widget",
            type="chart",
            source="conversations.csat",
            config={
                "type": "datalake_config",  # Different type
                "filter": {"flow": "csat_flow"},
                "op_field": "satisfaction_score",
            },
            position={},
        )

        result = get_csat_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_nps_human_widget_with_valid_widget(self):
        """Test get_nps_human_widget returns widget when valid NPS human widget exists"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS Human Widget",
            type="chart",
            source="conversations.nps",
            config={
                "type": "flow_result",
                "filter": {"flow": "nps_flow"},
                "op_field": "nps_score",
            },
            position={},
        )

        result = get_nps_human_widget(self.project)

        self.assertEqual(result, widget)
        self.assertEqual(result.source, "conversations.nps")
        self.assertEqual(result.config["type"], "flow_result")
        self.assertEqual(result.config["filter"]["flow"], "nps_flow")
        self.assertEqual(result.config["op_field"], "nps_score")

    def test_get_nps_human_widget_without_widget(self):
        """Test get_nps_human_widget returns None when no NPS human widget exists"""
        result = get_nps_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_nps_human_widget_without_flow(self):
        """Test get_nps_human_widget returns None when widget exists but has no flow"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS Human Widget",
            type="chart",
            source="conversations.nps",
            config={
                "type": "flow_result",
                "filter": {
                    # Missing flow
                },
                "op_field": "nps_score",
            },
            position={},
        )

        result = get_nps_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_nps_human_widget_without_op_field(self):
        """Test get_nps_human_widget returns None when widget exists but has no op_field"""
        widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="NPS Human Widget",
            type="chart",
            source="conversations.nps",
            config={
                "type": "flow_result",
                "filter": {"flow": "nps_flow"},
                # Missing op_field
            },
            position={},
        )

        result = get_nps_human_widget(self.project)
        self.assertIsNone(result)

    def test_get_custom_widgets_with_widgets(self):
        """Test get_custom_widgets returns list of UUIDs when custom widgets exist"""
        widget1 = Widget.objects.create(
            dashboard=self.dashboard,
            name="Custom Widget 1",
            type="chart",
            source="conversations.custom",
            config={},
            position={},
        )
        widget2 = Widget.objects.create(
            dashboard=self.dashboard,
            name="Custom Widget 2",
            type="table",
            source="conversations.custom",
            config={},
            position={},
        )
        # Create a non-custom widget that should not be included
        Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Widget",
            type="chart",
            source="conversations.csat",
            config={},
            position={},
        )

        result = get_custom_widgets(self.project)

        self.assertEqual(len(result), 2)
        self.assertIn(widget1.uuid, result)
        self.assertIn(widget2.uuid, result)

    def test_get_custom_widgets_without_widgets(self):
        """Test get_custom_widgets returns empty list when no custom widgets exist"""
        # Create a non-custom widget
        Widget.objects.create(
            dashboard=self.dashboard,
            name="CSAT Widget",
            type="chart",
            source="conversations.csat",
            config={},
            position={},
        )

        result = get_custom_widgets(self.project)
        self.assertEqual(len(result), 0)

    def test_get_custom_widgets_with_different_project(self):
        """Test get_custom_widgets only returns widgets for the specified project"""
        # Create another project and dashboard
        other_project = Project.objects.create(name="Other Project")
        other_dashboard = Dashboard.objects.create(
            project=other_project,
            name="Other Dashboard",
            description="Other Dashboard Description",
        )

        # Create custom widget for other project
        other_widget = Widget.objects.create(
            dashboard=other_dashboard,
            name="Other Custom Widget",
            type="chart",
            source="conversations.custom",
            config={},
            position={},
        )

        # Create custom widget for current project
        current_widget = Widget.objects.create(
            dashboard=self.dashboard,
            name="Current Custom Widget",
            type="chart",
            source="conversations.custom",
            config={},
            position={},
        )

        result = get_custom_widgets(self.project)

        self.assertEqual(len(result), 1)
        self.assertIn(current_widget.uuid, result)
        self.assertNotIn(other_widget.uuid, result)
