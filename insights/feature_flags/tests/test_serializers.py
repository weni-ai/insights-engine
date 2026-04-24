import uuid

from django.test import TestCase

from insights.feature_flags.serializers import (
    FeatureFlagsQueryParamsSerializer,
)
from insights.projects.models import Project


class FeatureFlagsQueryParamsSerializerTestCase(TestCase):
    def test_project_uuid_is_required(self):
        serializer = FeatureFlagsQueryParamsSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)

    def test_project_uuid_must_be_valid_uuid(self):
        serializer = FeatureFlagsQueryParamsSerializer(
            data={"project_uuid": "not-a-uuid"}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("project_uuid", serializer.errors)

    def test_validate_sets_project_to_none_when_project_does_not_exist(self):
        serializer = FeatureFlagsQueryParamsSerializer(
            data={"project_uuid": str(uuid.uuid4())}
        )

        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data["project"])

    def test_validate_populates_project_when_it_exists(self):
        project = Project.objects.create(name="Test")

        serializer = FeatureFlagsQueryParamsSerializer(
            data={"project_uuid": str(project.uuid)}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["project"], project)
