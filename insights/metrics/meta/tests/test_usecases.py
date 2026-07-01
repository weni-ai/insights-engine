import uuid

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
        self.project = Project.objects.create(name="Test Project")
        self.app_uuid = uuid.uuid4()
        self.waba_id = "1234567890"
        self.phone_number = {
            "id": "445303688657575",
            "display_phone_number": "+55 82 98877 6655",
        }

    def test_creates_dashboard_when_none_exists(self):
        self.assertFalse(
            Dashboard.objects.filter(
                project=self.project, config__is_whatsapp_integration=True
            ).exists()
        )

        dashboard = SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.project, self.project)
        self.assertEqual(
            dashboard.name, f"Meta {self.phone_number['display_phone_number']}"
        )
        self.assertEqual(dashboard.config["waba_id"], self.waba_id)
        self.assertEqual(dashboard.config["app_uuid"], str(self.app_uuid))
        self.assertEqual(dashboard.config["phone_number"], self.phone_number)
        self.assertTrue(dashboard.config["is_whatsapp_integration"])

    def test_returns_dashboard_with_expected_config(self):
        dashboard = SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(
            dashboard.config,
            {
                "is_whatsapp_integration": True,
                "app_uuid": str(self.app_uuid),
                "waba_id": self.waba_id,
                "phone_number": self.phone_number,
            },
        )

    def test_updates_existing_dashboard_when_phone_number_id_matches(self):
        existing = Dashboard.objects.create(
            project=self.project,
            name="Existing",
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

        dashboard = SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(dashboard.pk, existing.pk)
        self.assertEqual(dashboard.config["waba_id"], self.waba_id)
        self.assertEqual(dashboard.config["app_uuid"], str(self.app_uuid))
        self.assertEqual(dashboard.config["phone_number"], self.phone_number)

        self.assertEqual(
            Dashboard.objects.filter(
                project=self.project, config__is_whatsapp_integration=True
            ).count(),
            1,
        )

    def test_does_not_update_dashboard_from_a_different_project(self):
        other_project = Project.objects.create(name="Other Project")
        other_dashboard = Dashboard.objects.create(
            project=other_project,
            name="Other Dashboard",
            config={
                "is_whatsapp_integration": True,
                "app_uuid": str(uuid.uuid4()),
                "waba_id": "other_waba",
                "phone_number": self.phone_number,
            },
        )

        SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        other_dashboard.refresh_from_db()
        self.assertEqual(other_dashboard.config["waba_id"], "other_waba")

    def test_does_not_update_dashboard_with_different_phone_number_id(self):
        existing = Dashboard.objects.create(
            project=self.project,
            name="Other Phone Dashboard",
            config={
                "is_whatsapp_integration": True,
                "app_uuid": str(uuid.uuid4()),
                "waba_id": "other_waba",
                "phone_number": {
                    "id": "999999999999999",
                    "display_phone_number": "+55 99 99999 9999",
                },
            },
        )

        SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        existing.refresh_from_db()
        self.assertEqual(existing.config["waba_id"], "other_waba")
        self.assertEqual(
            Dashboard.objects.filter(
                project=self.project, config__is_whatsapp_integration=True
            ).count(),
            2,
        )

    def test_does_not_create_copy_when_no_main_project_in_org(self):
        org_uuid = uuid.uuid4()
        self.project.org_uuid = org_uuid
        self.project.save(update_fields=["org_uuid"])

        SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(
            Dashboard.objects.filter(
                config__is_whatsapp_integration=True,
                config__waba_id=self.waba_id,
            ).count(),
            1,
        )

    def test_creates_copy_in_main_project_when_it_exists(self):
        org_uuid = uuid.uuid4()
        secondary_project = Project.objects.create(
            name="Secondary Project",
            org_uuid=org_uuid,
            config={"is_secondary_project": True},
        )
        main_project = Project.objects.create(
            name="Main Project",
            org_uuid=org_uuid,
            config={"is_main_project": True},
        )

        SaveWhatsappIntegrationUseCase().execute(
            project=secondary_project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        secondary_dashboard = Dashboard.objects.filter(
            project=secondary_project, config__is_whatsapp_integration=True
        ).first()
        self.assertIsNotNone(secondary_dashboard)
        self.assertEqual(
            secondary_dashboard.name,
            f"Meta {self.phone_number['display_phone_number']}",
        )

        main_dashboard = Dashboard.objects.filter(
            project=main_project, config__is_whatsapp_integration=True
        ).first()
        self.assertIsNotNone(main_dashboard)
        self.assertEqual(
            main_dashboard.name,
            f"{secondary_project.name} {self.phone_number['display_phone_number']}",
        )
        self.assertEqual(main_dashboard.config["waba_id"], self.waba_id)
        self.assertEqual(main_dashboard.config["app_uuid"], str(self.app_uuid))

    def test_ignores_main_project_from_a_different_org(self):
        self.project.org_uuid = uuid.uuid4()
        self.project.save(update_fields=["org_uuid"])

        Project.objects.create(
            name="Main Project From Another Org",
            org_uuid=uuid.uuid4(),
            config={"is_main_project": True},
        )

        SaveWhatsappIntegrationUseCase().execute(
            project=self.project,
            app_uuid=self.app_uuid,
            waba_id=self.waba_id,
            phone_number=self.phone_number,
        )

        self.assertEqual(
            Dashboard.objects.filter(
                config__is_whatsapp_integration=True,
                config__waba_id=self.waba_id,
            ).count(),
            1,
        )


class TestRemoveWhatsappIntegrationUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.waba_id = "1234567890"

    def _create_whatsapp_dashboard(
        self, project: Project, waba_id: str, name: str = "Whatsapp Dashboard"
    ) -> Dashboard:
        return Dashboard.objects.create(
            project=project,
            name=name,
            config={
                "is_whatsapp_integration": True,
                "waba_id": waba_id,
            },
        )

    def test_removes_matching_dashboard(self):
        self._create_whatsapp_dashboard(self.project, self.waba_id)

        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=self.project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 1)
        self.assertFalse(
            Dashboard.objects.filter(
                project=self.project, config__is_whatsapp_integration=True
            ).exists()
        )

    def test_returns_zero_when_no_matching_dashboard_exists(self):
        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=self.project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 0)

    def test_does_not_remove_dashboard_with_different_waba_id(self):
        dashboard = self._create_whatsapp_dashboard(self.project, "other_waba")

        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=self.project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 0)
        self.assertTrue(Dashboard.objects.filter(pk=dashboard.pk).exists())

    def test_does_not_remove_dashboard_from_a_different_project(self):
        other_project = Project.objects.create(name="Other Project")
        other_dashboard = self._create_whatsapp_dashboard(other_project, self.waba_id)

        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=self.project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 0)
        self.assertTrue(Dashboard.objects.filter(pk=other_dashboard.pk).exists())

    def test_removes_dashboard_copy_from_main_project(self):
        org_uuid = uuid.uuid4()
        secondary_project = Project.objects.create(
            name="Secondary Project",
            org_uuid=org_uuid,
            config={"is_secondary_project": True},
        )
        main_project = Project.objects.create(
            name="Main Project",
            org_uuid=org_uuid,
            config={"is_main_project": True},
        )

        self._create_whatsapp_dashboard(secondary_project, self.waba_id)
        self._create_whatsapp_dashboard(
            main_project, self.waba_id, name="Main Copy"
        )

        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=secondary_project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 2)
        self.assertFalse(
            Dashboard.objects.filter(
                config__is_whatsapp_integration=True,
                config__waba_id=self.waba_id,
            ).exists()
        )

    def test_does_not_remove_main_project_dashboard_from_a_different_org(self):
        self.project.org_uuid = uuid.uuid4()
        self.project.save(update_fields=["org_uuid"])

        unrelated_main = Project.objects.create(
            name="Unrelated Main",
            org_uuid=uuid.uuid4(),
            config={"is_main_project": True},
        )
        unrelated_dashboard = self._create_whatsapp_dashboard(
            unrelated_main, self.waba_id
        )
        self._create_whatsapp_dashboard(self.project, self.waba_id)

        deleted_count = RemoveWhatsappIntegrationUseCase().execute(
            project=self.project, waba_id=self.waba_id
        )

        self.assertEqual(deleted_count, 1)
        self.assertTrue(Dashboard.objects.filter(pk=unrelated_dashboard.pk).exists())
