from django.test import TestCase
import datetime
import uuid

from insights.metrics.conversations.reports.serializers import (
    ConversationsReportQueryParamsSerializer,
)
from insights.projects.models import Project
from insights.reports.choices import ReportFormat
from insights.metrics.conversations.reports.choices import ConversationsReportSections
from insights.widgets.models import Widget
from insights.dashboards.models import Dashboard


class TestConversationsReportQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
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
        serializer = ConversationsReportQueryParamsSerializer(
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
            serializer.validated_data["start_date"], datetime.date(2025, 1, 24)
        )
        self.assertEqual(
            serializer.validated_data["end_date"], datetime.date(2025, 1, 25)
        )
        self.assertEqual(
            serializer.validated_data["sections"],
            [ConversationsReportSections.RESOLUTIONS],
        )

    def test_serializer_with_custom_widgets_and_without_sections(self):
        serializer = ConversationsReportQueryParamsSerializer(
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
            serializer.validated_data["start_date"], datetime.date(2025, 1, 24)
        )
        self.assertEqual(
            serializer.validated_data["end_date"], datetime.date(2025, 1, 25)
        )
        self.assertEqual(
            serializer.validated_data["custom_widgets"],
            [self.widget.uuid],
        )

    def test_serializer_without_custom_widgets_and_with_sections(self):
        serializer = ConversationsReportQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "type": ReportFormat.CSV,
                "start_date": "2025-01-24",
                "end_date": "2025-01-25",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["sections"][0].code, "sections_or_custom_widgets_required"
        )
        self.assertEqual(
            serializer.errors["custom_widgets"][0].code,
            "sections_or_custom_widgets_required",
        )

    def test_serializer_with_non_existent_project(self):
        serializer = ConversationsReportQueryParamsSerializer(
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
        serializer = ConversationsReportQueryParamsSerializer(
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
        serializer = ConversationsReportQueryParamsSerializer(
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
        serializer = ConversationsReportQueryParamsSerializer(
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
        serializer = ConversationsReportQueryParamsSerializer(
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
        serializer = ConversationsReportQueryParamsSerializer(
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
