from uuid import uuid4

import pytest

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
