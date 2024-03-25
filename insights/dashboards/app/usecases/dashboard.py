from dataclasses import dataclass, field
from datetime import datetime

from ...domain.entities import Dashboard
from ...domain.repositories import DashboardRepository


class CreateDashboardUseCase:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self.dashboard_repo = dashboard_repo

    def execute(self, permission=Dashboard) -> Dashboard:
        return self.dashboard_repo.create(permission)


@dataclass
class UpdateDashboardInput:
    role: int

    def __post_init__(self):
        self.updated_at = datetime.now()


class UpdateDashboardUseCase:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self.dashboard_repo = dashboard_repo

    def execute(self, uuid: str, fields: UpdateDashboardInput) -> Dashboard:
        return self.dashboard_repo.update(uuid=uuid, fields=fields.__dict__)


class DeleteDashboardUseCase:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self.dashboard_repo = dashboard_repo

    def execute(self, uuid: str) -> bool:
        return self.dashboard_repo.delete(uuid=uuid)


class GetDashboardUseCase:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self.dashboard_repo = dashboard_repo

    def execute(self, uuid: str) -> bool:
        return self.dashboard_repo.get(uuid=uuid)


@dataclass(frozen=True, slots=True)
class DashboardListInput:
    project: str | None = field(default=None)
    user: str | None = field(default=None)
    role: int | None = field(default=None)


@dataclass
class DashboardListSearchInput:
    page: int | None = None
    per_page: int | None = None
    sort: str | None = None
    filter: DashboardListInput | None = None


@dataclass(frozen=True)
class DashboardListOutput:
    items: list[Dashboard]
    total: int
    current_page: int
    per_page: int
    last_page: int


class ListDashboardUseCase:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self.dashboard_repo = dashboard_repo

    def execute(self, filters: DashboardListInput) -> DashboardListOutput:
        return self.dashboard_repo.filter(filters=filters)
