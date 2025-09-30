from unittest.mock import MagicMock
from insights.projects.models import Project
from insights.projects.services.indexer_activation import (
    BaseProjectIndexerActivationService,
)


class MockIndexerActivationService(BaseProjectIndexerActivationService):
    def is_project_active_on_indexer(self, project: Project) -> bool:
        return True

    def is_project_queued(self, project: Project) -> bool:
        return False

    def add_project_to_queue(self, project: Project) -> bool:
        return True

    def activate_project_on_indexer(self, project: Project) -> bool:
        return True

    def __init__(self):
        self.is_project_active_on_indexer = MagicMock(return_value=True)
        self.is_project_queued = MagicMock(return_value=False)
        self.add_project_to_queue = MagicMock(return_value=True)
        self.activate_project_on_indexer = MagicMock(return_value=True)
