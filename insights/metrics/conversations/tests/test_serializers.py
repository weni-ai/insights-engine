from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    ConversationsTimeseriesData,
    ConversationsTimeseriesMetrics,
)
from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
)
from insights.projects.models import Project


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


class TestConversationsTimeseriesDataSerializer(TestCase):
    def test_validate_data_for_day_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.DAY,
            total=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-01-02", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-01-02", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-01-02", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-01-02", "value": 200},
            ],
        )

    def test_validate_data_for_hour_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.HOUR,
            total=[
                ConversationsTimeseriesData(label="10h", value=100),
                ConversationsTimeseriesData(label="11h", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="10h", value=100),
                ConversationsTimeseriesData(label="11h", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "10h", "value": 100},
                {"label": "11h", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "10h", "value": 100},
                {"label": "11h", "value": 200},
            ],
        )

    def test_validate_data_for_month_unit(self):
        timeseries_metrics = ConversationsTimeseriesMetrics(
            unit=ConversationsTimeseriesUnit.MONTH,
            total=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-02-01", value=200),
            ],
            by_human=[
                ConversationsTimeseriesData(label="2021-01-01", value=100),
                ConversationsTimeseriesData(label="2021-02-01", value=200),
            ],
        )

        serializer = ConversationsTimeseriesMetricsSerializer(timeseries_metrics)

        self.assertEqual(serializer.data["unit"], ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            serializer.data["total"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-02-01", "value": 200},
            ],
        )
        self.assertEqual(
            serializer.data["by_human"],
            [
                {"label": "2021-01-01", "value": 100},
                {"label": "2021-02-01", "value": 200},
            ],
        )


class TestConversationsTimeseriesMetricsQueryParamsSerializer(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )

    def test_serializer(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["unit"], ConversationsTimeseriesUnit.DAY
        )
        self.assertEqual(serializer.validated_data["project"], self.project)
        self.assertEqual(str(serializer.validated_data["start_date"]), "2021-01-01")
        self.assertEqual(str(serializer.validated_data["end_date"]), "2021-01-02")

    def test_serializer_invalid_start_date(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-02",
                "end_date": "2021-01-01",
                "project_uuid": self.project.uuid,
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)
        self.assertEqual(
            serializer.errors["start_date"][0].code, "start_date_after_end_date"
        )

    def test_serializer_invalid_project_uuid(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)
        self.assertEqual(serializer.errors["project_uuid"][0].code, "project_not_found")

    def test_serializer_invalid_unit(self):
        serializer = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": self.project.uuid,
                "unit": "invalid_unit",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("unit", serializer.errors)
        self.assertEqual(serializer.errors["unit"][0].code, "invalid_choice")
