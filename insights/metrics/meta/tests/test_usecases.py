import uuid
from unittest.mock import patch

from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.meta.usecases.remove_whatsapp_integration import (
    RemoveWhatsappIntegrationUseCase,
)
from insights.metrics.meta.usecases.save_whatsapp_integration import (
    SaveWhatsappIntegrationUseCase,
)
from insights.projects.models import Project


class TestSaveWhatsappIntegrationUseCase(TestCase):
    def setUp(self):
        self.use_case = SaveWhatsappIntegrationUseCase()
        self.app_uuid = uuid.uuid4()
        self.waba_id = "1234567890"
        self.phone_number = {
            "id": "445303688657575",
            "display_phone_number": "+55 82 98877 6655",
        }

    def test_execute_creates_new_dashboard_when_none_exists(self):
        project = Project.objects.create(name="Test Project")

        dashboard = self.use_case.execute(
            project_uuid=project.uuid,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(dashboard.project, project)
        self.assertEqual(dashboard.name, "Meta +55 82 98877 6655")
        self.assertEqual(
            dashboard.config,
            {
                "is_whatsapp_integration": True,
                "app_uuid": str(self.app_uuid),
                "waba_id": self.waba_id,
                "phone_number": self.phone_number,
            },
        )

    def test_execute_updates_existing_dashboard_when_phone_number_id_matches(self):
        project = Project.objects.create(name="Test Project")
        existing = Dashboard.objects.create(
            project=project,
            name="Old name",
            config={
                "is_whatsapp_integration": True,
                "app_uuid": str(uuid.uuid4()),
                "waba_id": "old_waba",
                "phone_number": {
                    "id": self.phone_number["id"],
                    "display_phone_number": "+55 11 11111 1111",
                },
            },
        )

        dashboard = self.use_case.execute(
            project_uuid=project.uuid,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        existing.refresh_from_db()
        self.assertEqual(dashboard.pk, existing.pk)
        self.assertEqual(existing.name, "Old name")
        self.assertEqual(existing.config["waba_id"], self.waba_id)
        self.assertEqual(existing.config["app_uuid"], str(self.app_uuid))
        self.assertEqual(
            existing.config["phone_number"]["display_phone_number"],
            self.phone_number["display_phone_number"],
        )

    def test_execute_does_not_match_dashboard_with_different_phone_number_id(self):
        project = Project.objects.create(name="Test Project")
        Dashboard.objects.create(
            project=project,
            name="Other phone",
            config={
                "is_whatsapp_integration": True,
                "app_uuid": str(uuid.uuid4()),
                "waba_id": "other_waba",
                "phone_number": {
                    "id": "999999999999999",
                    "display_phone_number": "+55 11 22222 3333",
                },
            },
        )

        dashboard = self.use_case.execute(
            project_uuid=project.uuid,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(
            Dashboard.objects.filter(
                project=project, config__is_whatsapp_integration=True
            ).count(),
            2,
        )
        self.assertEqual(dashboard.name, "Meta +55 82 98877 6655")

    def test_execute_creates_copy_in_main_project_when_org_has_main_project(self):
        org_uuid = uuid.uuid4()
        project = Project.objects.create(name="Secondary Project", org_uuid=org_uuid)
        main_project = Project.objects.create(
            name="Main Project",
            org_uuid=org_uuid,
            config={"is_main_project": True},
        )

        self.use_case.execute(
            project_uuid=project.uuid,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        primary = Dashboard.objects.filter(
            project=project, config__is_whatsapp_integration=True
        ).first()
        self.assertIsNotNone(primary)
        self.assertEqual(primary.name, "Meta +55 82 98877 6655")

        copy = Dashboard.objects.filter(
            project=main_project, config__is_whatsapp_integration=True
        ).first()
        self.assertIsNotNone(copy)
        self.assertEqual(copy.name, "Secondary Project +55 82 98877 6655")
        self.assertEqual(copy.config["waba_id"], self.waba_id)
        self.assertEqual(copy.config["app_uuid"], str(self.app_uuid))

    def test_execute_does_not_create_copy_when_no_main_project_exists(self):
        org_uuid = uuid.uuid4()
        project = Project.objects.create(name="Secondary Project", org_uuid=org_uuid)
        Project.objects.create(name="Sibling Project", org_uuid=org_uuid)

        self.use_case.execute(
            project_uuid=project.uuid,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(
            Dashboard.objects.filter(config__is_whatsapp_integration=True).count(),
            1,
        )

    def test_execute_propagates_exception_when_project_does_not_exist(self):
        with self.assertRaises(Project.DoesNotExist):
            self.use_case.execute(
                project_uuid=uuid.uuid4(),
                app_uuid=self.app_uuid,
                waba_id=self.waba_id,
                phone_number=self.phone_number,
            )

    def test_execute_propagates_database_exception(self):
        project = Project.objects.create(name="Test Project")

        with patch(
            "insights.metrics.meta.usecases.save_whatsapp_integration."
            "Dashboard.objects.create",
            side_effect=RuntimeError("db error"),
        ):
            with self.assertRaises(RuntimeError):
                self.use_case.execute(
                    project_uuid=project.uuid,
                    app_uuid=self.app_uuid,
                    waba_id=self.waba_id,
                    phone_number=self.phone_number,
                )


class TestRemoveWhatsappIntegrationUseCase(TestCase):
    def setUp(self):
        self.use_case = RemoveWhatsappIntegrationUseCase()
        self.waba_id = "1234567890"

    def test_execute_deletes_matching_dashboard(self):
        project = Project.objects.create(name="Test Project")
        Dashboard.objects.create(
            project=project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.waba_id,
            },
        )

        deleted = self.use_case.execute(
            project_uuid=project.uuid, waba_id=self.waba_id
        )

        self.assertEqual(deleted, 1)
        self.assertFalse(
            Dashboard.objects.filter(
                project=project, config__waba_id=self.waba_id
            ).exists()
        )

    def test_execute_also_deletes_copy_in_main_project(self):
        org_uuid = uuid.uuid4()
        project = Project.objects.create(name="Secondary Project", org_uuid=org_uuid)
        main_project = Project.objects.create(
            name="Main Project",
            org_uuid=org_uuid,
            config={"is_main_project": True},
        )

        Dashboard.objects.create(
            project=project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.waba_id,
            },
        )
        Dashboard.objects.create(
            project=main_project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.waba_id,
            },
        )

        deleted = self.use_case.execute(
            project_uuid=project.uuid, waba_id=self.waba_id
        )

        self.assertEqual(deleted, 2)
        self.assertFalse(
            Dashboard.objects.filter(config__waba_id=self.waba_id).exists()
        )

    def test_execute_does_not_delete_dashboards_with_other_waba_id(self):
        project = Project.objects.create(name="Test Project")
        other_dashboard = Dashboard.objects.create(
            project=project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": "other_waba",
            },
        )

        deleted = self.use_case.execute(
            project_uuid=project.uuid, waba_id=self.waba_id
        )

        self.assertEqual(deleted, 0)
        self.assertTrue(Dashboard.objects.filter(pk=other_dashboard.pk).exists())

    def test_execute_does_not_delete_dashboards_from_other_projects(self):
        org_uuid = uuid.uuid4()
        project = Project.objects.create(name="Secondary Project", org_uuid=org_uuid)
        unrelated_project = Project.objects.create(
            name="Unrelated Project", org_uuid=uuid.uuid4()
        )

        unrelated_dashboard = Dashboard.objects.create(
            project=unrelated_project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.waba_id,
            },
        )

        deleted = self.use_case.execute(
            project_uuid=project.uuid, waba_id=self.waba_id
        )

        self.assertEqual(deleted, 0)
        self.assertTrue(Dashboard.objects.filter(pk=unrelated_dashboard.pk).exists())

    def test_execute_returns_zero_when_no_dashboard_matches(self):
        project = Project.objects.create(name="Test Project")

        deleted = self.use_case.execute(
            project_uuid=project.uuid, waba_id=self.waba_id
        )

        self.assertEqual(deleted, 0)

    def test_execute_propagates_database_exception(self):
        project = Project.objects.create(name="Test Project")
        Dashboard.objects.create(
            project=project,
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.waba_id,
            },
        )

        with patch(
            "insights.metrics.meta.usecases.remove_whatsapp_integration."
            "Dashboard.objects.filter",
            side_effect=RuntimeError("db error"),
        ):
            with self.assertRaises(RuntimeError):
                self.use_case.execute(
                    project_uuid=project.uuid, waba_id=self.waba_id
                )
