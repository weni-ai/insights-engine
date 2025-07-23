import uuid
from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.conversations.enums import CsatMetricsType
from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    CsatMetricsQueryParamsSerializer,
)
from insights.widgets.models import Widget


class TestConversationBaseQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("project", serializer.validated_data)
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

    def test_serializer_invalid_start_date(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")


class TestCsatMetricsQueryParamsSerializer(TestCase):
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
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "csat",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

    def test_serializer(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": self.widget.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": CsatMetricsType.HUMAN,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            str(serializer.validated_data["project_uuid"]), str(self.project.uuid)
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")
        self.assertEqual(serializer.validated_data["type"], CsatMetricsType.HUMAN)
        self.assertEqual(serializer.validated_data["widget"], self.widget)

    def test_serializer_invalid_type(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": self.widget.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": "invalid",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")

    def test_serializer_invalid_widget_uuid(self):
        serializer = CsatMetricsQueryParamsSerializer(
            data={
                "project_uuid": self.project.uuid,
                "widget_uuid": uuid.uuid4(),
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": CsatMetricsType.HUMAN,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("widget_uuid", serializer.errors)
        self.assertEqual(serializer.errors["widget_uuid"][0].code, "widget_not_found")
