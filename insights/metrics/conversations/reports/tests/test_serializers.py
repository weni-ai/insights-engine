from django.test import TestCase
import datetime
import uuid
import pytz

from insights.metrics.conversations.reports.serializers import (
    RequestConversationsReportGenerationSerializer,
    GetConversationsReportStatusQueryParamsSerializer,
)
from insights.projects.models import Project
from insights.reports.choices import ReportFormat
from insights.metrics.conversations.reports.choices import ConversationsReportSections
from insights.widgets.models import Widget
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard


class TestGetConversationsReportStatusQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = GetConversationsReportStatusQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["project"], self.project)

    def test_serializer_with_non_existent_project(self):
        serializer = GetConversationsReportStatusQueryParamsSerializer(
            data={
                "project_uuid": uuid.uuid4(),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestRequestConversationsReportGenerationSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name=CONVERSATIONS_DASHBOARD_NAME,
        )
        self.widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "key": "test_key",
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

    def test_serializer(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.RESOLUTIONS],
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(serializer.validated_data["type"], ReportFormat.CSV)
        self.assertEqual(
            serializer.validated_data["start"],
            datetime.datetime(
                2025,
                1,
                24,
                0,
                0,
                0,
                tzinfo=(
                    pytz.timezone(self.project.timezone)
                    if self.project.timezone
                    else pytz.UTC
                ),
            ),
        )
        self.assertEqual(
            serializer.validated_data["end"],
            datetime.datetime(
                2025,
                1,
                25,
                23,
                59,
                59,
                tzinfo=(
                    pytz.timezone(self.project.timezone)
                    if self.project.timezone
                    else pytz.UTC
                ),
            ),
        )
        self.assertEqual(
            serializer.validated_data["sections"],
            [ConversationsReportSections.RESOLUTIONS],
        )

    def test_serializer_with_custom_widgets_and_without_sections(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "custom_widgets": [self.widget.uuid],
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(serializer.validated_data["type"], ReportFormat.CSV)
        self.assertEqual(
            serializer.validated_data["start"],
            datetime.datetime(
                2025,
                1,
                24,
                0,
                0,
                0,
                tzinfo=(
                    pytz.timezone(self.project.timezone)
                    if self.project.timezone
                    else pytz.UTC
                ),
            ),
        )
        self.assertEqual(
            serializer.validated_data["end"],
            datetime.datetime(
                2025,
                1,
                25,
                23,
                59,
                59,
                tzinfo=(
                    pytz.timezone(self.project.timezone)
                    if self.project.timezone
                    else pytz.UTC
                ),
            ),
        )
        self.assertEqual(
            serializer.validated_data["custom_widgets"],
            [self.widget.uuid],
        )

    def test_serializer_without_custom_widgets_and_with_sections(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code, "sections_or_custom_widgets_required"
        )
        self.assertEqual(
            serializer.errors["error"][0].code,
            "sections_or_custom_widgets_required",
        )

    def test_serializer_with_non_existent_project(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": uuid.uuid4(),
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.RESOLUTIONS],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")

    def test_serializer_with_non_existent_custom_widgets(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "custom_widgets": [uuid.uuid4()],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors["custom_widgets"]), 1)
        self.assertEqual(
            serializer.errors["custom_widgets"][0].code, "widgets_not_found"
        )

    def test_serializer_with_custom_widgets_from_another_project(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=Dashboard.objects.create(
                name="Test Dashboard",
                project=Project.objects.create(name="Another Project"),
            ),
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "key": "test_key",
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "custom_widgets": [
                    self.widget.uuid,
                    widget.uuid,
                ],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors["custom_widgets"]), 1)
        self.assertEqual(
            serializer.errors["custom_widgets"][0].code, "widgets_not_found"
        )

    def test_serializer_with_start_date_after_end_date(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-25",
                "end_date": "2025-01-24",
                "sections": [ConversationsReportSections.RESOLUTIONS],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_with_invalid_type(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": "PDF",
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.RESOLUTIONS],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")

    def test_serializer_with_invalid_sections(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": ["INVALID"],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["sections"][0][0].code, "invalid_choice")

    def test_serializer_with_csat_ai_section_and_csat_ai_widget(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_AI],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["error"][0].code, "csat_ai_widget_not_found")

    def test_serializer_with_csat_ai_section_and_csat_ai_widget_without_agent_uuid(
        self,
    ):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "type": "CSAT",
                },
            },
        )

        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_AI],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code,
            "csat_ai_widget_not_found",
        )

    def test_serializer_with_csat_ai_section_and_csat_ai_widget_with_agent_uuid(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "type": "CSAT",
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_AI],
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["source_config"]["csat_ai_agent_uuid"],
            widget.config.get("datalake_config", {}).get("agent_uuid"),
        )

    def test_serializer_with_nps_ai_section_and_nps_ai_widget(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_AI],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["error"][0].code, "nps_ai_widget_not_found")

    def test_serializer_with_nps_ai_section_and_nps_ai_widget_without_agent_uuid(self):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.nps",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "type": "NPS",
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_AI],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code,
            "nps_ai_widget_not_found",
        )

    def test_serializer_with_csat_human_section_and_csat_human_widget(self):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_HUMAN],
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code, "csat_human_widget_not_found"
        )

    def test_serializer_with_csat_human_section_and_csat_human_widget_without_flow_uuid(
        self,
    ):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "filter": {
                    "op_field": "csat",
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_HUMAN],
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code,
            "csat_human_widget_not_found",
        )

    def test_serializer_with_csat_human_section_and_csat_human_widget_without_op_field(
        self,
    ):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "filter": {
                    "flow": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_HUMAN],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code,
            "csat_human_widget_not_found",
        )

    def test_serializer_with_csat_human_section_and_csat_human_widget_with_flow_uuid(
        self,
    ):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.csat",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "op_field": "user_feedback",
                "filter": {
                    "flow": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.CSAT_HUMAN],
            }
        )

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data["source_config"]["csat_human_flow_uuid"],
            widget.config.get("filter", {}).get("flow"),
        )

    def test_serializer_with_nps_human_section_and_without_nps_widget(
        self,
    ):
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_HUMAN],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code, "nps_human_widget_not_found"
        )

    def test_serializer_with_nps_human_section_and_nps_human_widget_without_flow_uuid(
        self,
    ):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.nps",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "filter": {
                    "op_field": "user_feedback",
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_HUMAN],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code,
            "nps_human_widget_not_found",
        )

    def test_serializer_with_nps_human_section_and_nps_human_widget_without_op_field(
        self,
    ):
        Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.nps",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "filter": {
                    "flow": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_HUMAN],
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["error"][0].code, "nps_human_widget_not_found"
        )

    def test_serializer_with_nps_human_section_and_nps_human_widget_with_flow_uuid_and_op_field(
        self,
    ):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.nps",
            type="flow_result",
            position=[1, 2],
            config={
                "type": "flow_result",
                "op_field": "user_feedback",
                "filter": {
                    "flow": str(uuid.uuid4()),
                },
            },
        )
        serializer = RequestConversationsReportGenerationSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
                "sections": [ConversationsReportSections.NPS_HUMAN],
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["source_config"]["nps_human_flow_uuid"],
            widget.config.get("filter", {}).get("flow"),
        )
        self.assertEqual(
            serializer.validated_data["source_config"]["nps_human_op_field"],
            widget.config.get("op_field"),
        )
