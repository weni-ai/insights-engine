from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO


class TestCreateProjectUseCase(TestCase):
    def test_create_project(self):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        self.assertEqual(project.uuid, project_dto.uuid)
        self.assertIsNone(project.vtex_account)
        self.assertFalse(project.is_nexus_multi_agents_active)

    def test_create_project_with_vtex_account(self):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
            vtex_account="test_vtex_account",
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        self.assertEqual(project.uuid, project_dto.uuid)
        self.assertEqual(project.vtex_account, project_dto.vtex_account)

    def test_create_project_with_inline_agent_switch_enabled(self):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
            inline_agent_switch=True,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        self.assertEqual(project.uuid, project_dto.uuid)
        self.assertTrue(project.is_nexus_multi_agents_active)

    def test_create_project_with_inline_agent_switch_disabled(self):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
            inline_agent_switch=False,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        self.assertEqual(project.uuid, project_dto.uuid)
        self.assertFalse(project.is_nexus_multi_agents_active)

    @patch(
        "insights.projects.usecases.create.handle_project_created_with_inline_agent_switch"
    )
    @patch("insights.projects.usecases.create.create_conversation_dashboard")
    def test_create_project_dispatches_conversation_dashboard_task(
        self, mock_create_dashboard, mock_handle_inline
    ):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        mock_create_dashboard.delay.assert_called_once_with(project.uuid)
        mock_handle_inline.delay.assert_not_called()

    @patch(
        "insights.projects.usecases.create.handle_project_created_with_inline_agent_switch"
    )
    @patch("insights.projects.usecases.create.create_conversation_dashboard")
    def test_create_project_dispatches_inline_agent_switch_task_when_enabled(
        self, mock_create_dashboard, mock_handle_inline
    ):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
            inline_agent_switch=True,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        mock_create_dashboard.delay.assert_called_once_with(project.uuid)
        mock_handle_inline.delay.assert_called_once_with(project.uuid)

    @patch(
        "insights.projects.usecases.create.handle_project_created_with_inline_agent_switch"
    )
    @patch("insights.projects.usecases.create.create_conversation_dashboard")
    def test_create_project_does_not_dispatch_inline_agent_switch_task_when_disabled(
        self, mock_create_dashboard, mock_handle_inline
    ):
        project_dto = ProjectCreationDTO(
            uuid=uuid4().hex,
            name="test_name",
            timezone="America/Bahia",
            date_format="DD/MM/YYYY",
            is_template=False,
            inline_agent_switch=False,
        )

        project = ProjectsUseCase().create_project(project_dto=project_dto)

        mock_create_dashboard.delay.assert_called_once_with(project.uuid)
        mock_handle_inline.delay.assert_not_called()
