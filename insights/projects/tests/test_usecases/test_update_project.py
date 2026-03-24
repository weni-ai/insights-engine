from uuid import uuid4

from django.test import TestCase

from insights.projects.models import Project
from insights.projects.usecases.update import UpdateProjectUseCase


class TestUpdateProjectUseCase(TestCase):
    def setUp(self):
        self.use_case = UpdateProjectUseCase()
        self.project = Project.objects.create(
            name="Test Project",
            timezone="UTC",
            date_format="MM/DD/YYYY",
        )

    def test_update_name(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            name="Updated Name",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated Name")

    def test_update_timezone(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            timezone="America/Sao_Paulo",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.timezone, "America/Sao_Paulo")

    def test_update_date_format(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            date_format="DD/MM/YYYY",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.date_format, "DD/MM/YYYY")

    def test_update_multiple_fields(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            name="New Name",
            timezone="America/Bahia",
            date_format="YYYY-MM-DD",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "New Name")
        self.assertEqual(self.project.timezone, "America/Bahia")
        self.assertEqual(self.project.date_format, "YYYY-MM-DD")

    def test_unset_fields_remain_unchanged(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            name="Only Name Changed",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Only Name Changed")
        self.assertEqual(self.project.timezone, "UTC")
        self.assertEqual(self.project.date_format, "MM/DD/YYYY")

    def test_update_config_on_project_without_config(self):
        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            config={"key": "value"},
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.config, {"key": "value"})

    def test_update_config_merges_with_existing(self):
        self.project.config = {"existing_key": "existing_value"}
        self.project.save(update_fields=["config"])

        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            config={"new_key": "new_value"},
        )
        self.project.refresh_from_db()
        self.assertEqual(
            self.project.config,
            {"existing_key": "existing_value", "new_key": "new_value"},
        )

    def test_update_config_overwrites_existing_keys(self):
        self.project.config = {"key": "old_value", "other": "keep"}
        self.project.save(update_fields=["config"])

        self.use_case.execute(
            project_uuid=str(self.project.uuid),
            config={"key": "new_value"},
        )
        self.project.refresh_from_db()
        self.assertEqual(
            self.project.config,
            {"key": "new_value", "other": "keep"},
        )

    def test_raises_exception_for_nonexistent_project(self):
        with self.assertRaises(Exception):
            self.use_case.execute(project_uuid=str(uuid4()))
