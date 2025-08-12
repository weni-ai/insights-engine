import uuid

from django.test import TestCase, override_settings

from insights.projects.models import Project
from insights.projects.services.indexer_activation import (
    ProjectIndexerActivationService,
)

PROJECT_UUID = uuid.uuid4()


class TestIndexerActivationService(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            uuid=PROJECT_UUID,
            is_allowed=False,
        )
        self.service = ProjectIndexerActivationService()

    def test_is_project_active_on_indexer_when_project_is_not_allowed_and_not_in_allow_list(
        self,
    ):
        self.assertFalse(self.service.is_project_active_on_indexer(self.project))

    def test_is_project_active_on_indexer_when_project_is_allowed(self):
        self.project.is_allowed = True
        self.project.save(update_fields=["is_allowed"])
        self.assertTrue(self.service.is_project_active_on_indexer(self.project))

    @override_settings(PROJECT_ALLOW_LIST=[PROJECT_UUID])
    def test_is_project_active_on_indexer_when_project_is_not_allowed_and_in_allow_list(
        self,
    ):
        self.assertTrue(self.service.is_project_active_on_indexer(self.project))
