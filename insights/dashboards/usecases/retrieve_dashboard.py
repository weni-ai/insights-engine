from dataclasses import dataclass

from typing import List

from insights.dashboards.models import Dashboard


@dataclass
class DashFiltersDTO:
    project: str
    uuid: str = None
    name: str = None
    description: str = None

    def asdict(self):

        return {k: str(v) for k, v in self.__dict__.items() if v is not None}


class DashboardRetrieveUseCase:
    def __init__(self, storage_manager=Dashboard.objects) -> None:
        self.storage_manager = storage_manager

    def get(self, pk):
        return self.storage_manager.get(pk=pk)

    def list(
        self,
        filters: DashFiltersDTO,
        ordering: List[str] = [],
    ):
        query = self.storage_manager.filter(filters.asdict())
        if ordering != []:
            query = query.order_by(*ordering)

        return query
