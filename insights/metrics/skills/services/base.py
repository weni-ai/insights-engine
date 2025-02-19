from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from insights.projects.models import Project


class BaseSkillMetricsService(ABC):
    def __init__(self, project: "Project", filters: dict):
        self.project = project
        self.filters = filters

    @abstractmethod
    def validate_filters(self, filters: dict):
        pass

    @abstractmethod
    def get_metrics(self):
        pass
