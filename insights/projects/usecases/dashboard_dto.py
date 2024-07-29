from dataclasses import dataclass
from insights.projects.usecases.project_dto import ProjectCreationDTO


@dataclass
class FlowsDashboardCreationDTO:
    project: ProjectCreationDTO
    dashboard_name: str
    funnel_amount: int
    currency_type: str
