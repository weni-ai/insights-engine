from django.test import TestCase

from insights.projects.dataclass import UnlinkedProject
from insights.projects.models import Project
from insights.projects.usecases.update_vtex_account import UpdateProjectVTEXAccount


class TestUpdateProjectVTEXAccount(TestCase):
    def setUp(self):
        self.use_case = UpdateProjectVTEXAccount()
        self.project = Project.objects.create(
            name="Alphabet",
            vtex_account="abc",
        )

    def test_updates_vtex_account(self):
        self.use_case.execute(project=self.project, vtex_account="xyz")

        self.project.refresh_from_db()
        self.assertEqual(self.project.vtex_account, "xyz")

    def test_returns_project_instance_and_unlinked_list(self):
        result_project, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account="xyz"
        )

        self.assertIs(result_project, self.project)
        self.assertEqual(projects_unlinked, [])

    def test_logs_change_with_user_email(self):
        user_email = "example@vtex.com"

        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            self.use_case.execute(
                project=self.project,
                vtex_account="xyz",
                user_email=user_email,
            )

        expected_message = (
            f"[UpdateProjectVTEXAccount] VTEX Account for project "
            f"{self.project.name} ({self.project.uuid}) changed from "
            f"'abc' to 'xyz' by {user_email}"
        )

        self.assertIn(expected_message, logs.output[0])

    def test_logs_change_as_internal_when_user_email_is_none(self):
        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            self.use_case.execute(
                project=self.project,
                vtex_account="xyz",
                user_email=None,
            )

        expected_message = (
            f"[UpdateProjectVTEXAccount] VTEX Account for project "
            f"{self.project.name} ({self.project.uuid}) changed from "
            f"'abc' to 'xyz' by INTERNAL"
        )

        self.assertIn(expected_message, logs.output[0])

    def test_logs_change_as_internal_when_user_email_is_empty(self):
        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            self.use_case.execute(
                project=self.project,
                vtex_account="xyz",
                user_email="",
            )

        expected_message = (
            f"[UpdateProjectVTEXAccount] VTEX Account for project "
            f"{self.project.name} ({self.project.uuid}) changed from "
            f"'abc' to 'xyz' by INTERNAL"
        )

        self.assertIn(expected_message, logs.output[0])

    def test_removes_vtex_account_from_other_projects(self):
        other_project = Project.objects.create(
            name="Other",
            vtex_account="xyz",
        )

        _, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account="xyz"
        )

        other_project.refresh_from_db()
        self.assertIsNone(other_project.vtex_account)
        self.assertEqual(projects_unlinked, [
            UnlinkedProject(uuid=str(other_project.uuid), name="Other"),
        ])

    def test_removes_vtex_account_from_multiple_conflicting_projects(self):
        other_a = Project.objects.create(name="Other A", vtex_account="xyz")
        other_b = Project.objects.create(name="Other B", vtex_account="xyz")

        _, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account="xyz"
        )

        other_a.refresh_from_db()
        other_b.refresh_from_db()
        self.assertIsNone(other_a.vtex_account)
        self.assertIsNone(other_b.vtex_account)

        unlinked_uuids = {p.uuid for p in projects_unlinked}
        self.assertEqual(unlinked_uuids, {str(other_a.uuid), str(other_b.uuid)})

    def test_logs_removed_projects(self):
        other_project = Project.objects.create(
            name="Other",
            vtex_account="xyz",
        )

        with self.assertLogs(
            "insights.projects.usecases.update_vtex_account", level="INFO"
        ) as logs:
            self.use_case.execute(
                project=self.project,
                vtex_account="xyz",
                user_email="example@vtex.com",
            )

        removal_message = (
            f"[UpdateProjectVTEXAccount] Removed VTEX Account 'xyz' "
            f"from project {other_project.name} ({other_project.uuid}) "
            f"by example@vtex.com"
        )

        self.assertTrue(
            any(removal_message in line for line in logs.output),
        )

    def test_does_not_remove_when_vtex_account_is_empty(self):
        other_project = Project.objects.create(
            name="Other",
            vtex_account="",
        )

        _, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account=""
        )

        other_project.refresh_from_db()
        self.assertEqual(other_project.vtex_account, "")
        self.assertEqual(projects_unlinked, [])

    def test_does_not_remove_when_vtex_account_is_none(self):
        other_project = Project.objects.create(
            name="Other",
            vtex_account=None,
        )

        _, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account=None
        )

        other_project.refresh_from_db()
        self.assertIsNone(other_project.vtex_account)
        self.assertEqual(projects_unlinked, [])

    def test_no_removal_when_no_conflicts(self):
        other_project = Project.objects.create(
            name="Other",
            vtex_account="xyz",
        )

        _, projects_unlinked = self.use_case.execute(
            project=self.project, vtex_account="def"
        )

        other_project.refresh_from_db()
        self.assertEqual(other_project.vtex_account, "xyz")
        self.assertEqual(projects_unlinked, [])
