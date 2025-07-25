from datetime import datetime, time
from django.test import TestCase

from insights.projects.models import Project
from insights.metrics.conversations.serializers import (
    ConversationBaseQueryParamsSerializer,
)


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

        # Test that start_date is converted to datetime at midnight
        start_date = serializer.validated_data["start_date"]
        self.assertIsInstance(start_date, datetime)
        self.assertIsNotNone(start_date.tzinfo)  # Should be timezone-aware
        self.assertEqual(start_date.time(), time.min)  # Should be 00:00:00
        self.assertEqual(start_date.date().isoformat(), "2021-01-01")

        # Test that end_date is converted to datetime at 23:59:59
        end_date = serializer.validated_data["end_date"]
        self.assertIsInstance(end_date, datetime)
        self.assertIsNotNone(end_date.tzinfo)  # Should be timezone-aware
        self.assertEqual(end_date.time(), time(23, 59, 59))  # Should be 23:59:59
        self.assertEqual(end_date.date().isoformat(), "2021-01-02")

    def test_serializer_with_timezone(self):
        # Create a project with a specific timezone
        project_with_tz = Project.objects.create(
            name="Test Project with TZ", timezone="America/New_York"
        )

        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": project_with_tz.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Check that timezone is correctly applied
        self.assertEqual(str(start_date.tzinfo), "America/New_York")
        self.assertEqual(str(end_date.tzinfo), "America/New_York")

        # Check times are correct
        self.assertEqual(start_date.time(), time.min)
        self.assertEqual(end_date.time(), time(23, 59, 59))

    def test_serializer_without_timezone(self):
        # Create a project without timezone (should default to UTC)
        project_no_tz = Project.objects.create(name="Test Project No TZ", timezone="")

        serializer = ConversationBaseQueryParamsSerializer(
            data={
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "project_uuid": project_no_tz.uuid,
            }
        )
        self.assertTrue(serializer.is_valid())

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Check that UTC timezone is applied when no timezone is set
        self.assertEqual(str(start_date.tzinfo), "UTC")
        self.assertEqual(str(end_date.tzinfo), "UTC")

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
