from django.test import TestCase

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

    def test_returns_project_instance(self):
        result = self.use_case.execute(project=self.project, vtex_account="xyz")

        self.assertIs(result, self.project)

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
