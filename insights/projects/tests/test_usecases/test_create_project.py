from uuid import uuid4

import pytest

from insights.projects.usecases.create import ProjectsUseCase
from insights.projects.usecases.project_dto import ProjectCreationDTO
from insights.dashboards.models import DashboardTemplate


@pytest.mark.django_db
def test_create_project(monkeypatch):
    project_dto = ProjectCreationDTO(
        uuid=uuid4().hex,
        name="test_name",
        timezone="America/Bahia",
        date_format="DD/MM/YYYY",
        is_template=False,
    )

    # quando chega no filter do dashboard template no create_project, ele vem pra essa mock_filter e recebe o return dessa função
    # mock para evitar dar o erro durante a criação do projeto que agora chama a criação de dashboard junto.
    # dessa forma também ja testei o create em DashboardUseCase, pois caso esse teste passe, significa que
    # o create dos dashboards foram realizados e deu tudo certo.
    def mock_filter(*args, **kwargs):
        dashboard_templates = []
        for template_data in [
            {
                "name": "atendimento humano",
                "description": "dashboard de atendimento humano",
            },
            {"name": "jornada do bot", "description": "dashboard de jornada do bot"},
        ]:
            dashboard_template = DashboardTemplate.objects.create(
                name=template_data["name"],
                description=template_data["description"],
                project=None,
            )
            dashboard_templates.append(dashboard_template)
        return dashboard_templates

    monkeypatch.setattr(DashboardTemplate.objects, "filter", mock_filter)

    project = ProjectsUseCase().create_project(project_dto=project_dto)

    assert project.uuid == project_dto.uuid
