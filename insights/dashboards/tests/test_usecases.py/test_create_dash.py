import pytest

from insights.dashboards.usecases.create_dashboard import (
    DashboardCreateUseCase,
)
from insights.dashboards.usecases.dashboard_dto import DashboardCreationDTO


@pytest.mark.django_db
def test_create_dashboard(create_project):
    project = create_project
    dashboard_dto = DashboardCreationDTO(
        project=str(project.uuid),
        name="Atendimento Humano",
        description="Data that comes from the chats app",
        is_default=True,
        from_template=False,
        template=None,
    )
    dashboard = DashboardCreateUseCase().execute(dashboard_dto)
    assert dashboard.project == project
