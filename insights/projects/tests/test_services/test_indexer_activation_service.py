import uuid
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
import requests

from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import Project, ProjectIndexerActivation
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
        self.service = ProjectIndexerActivationService(retry_delay=0)

    def test_is_project_active_on_indexer_when_project_is_not_allowed_and_not_in_allow_list(
        self,
    ):
        self.assertFalse(self.service.is_project_active_on_indexer(self.project))

    def test_is_project_active_on_indexer_when_project_is_allowed(self):
        self.project.is_allowed = True
        self.project.save(update_fields=["is_allowed"])
        self.assertTrue(self.service.is_project_active_on_indexer(self.project))

    @override_settings(PROJECT_ALLOW_LIST=[str(PROJECT_UUID)])
    def test_is_project_active_on_indexer_when_project_is_not_allowed_and_in_allow_list(
        self,
    ):
        self.assertTrue(self.service.is_project_active_on_indexer(self.project))

    def test_add_project_to_queue_when_project_is_not_allowed_and_not_in_queue(self):
        self.assertFalse(
            ProjectIndexerActivation.objects.filter(
                project=self.project,
                status=ProjectIndexerActivationStatus.PENDING,
            ).exists()
        )

        self.assertTrue(self.service.add_project_to_queue(self.project))

        self.assertTrue(
            ProjectIndexerActivation.objects.filter(
                project=self.project,
                status=ProjectIndexerActivationStatus.PENDING,
            ).exists()
        )

    def test_is_project_queued_when_project_is_queued(self):
        ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        self.assertTrue(self.service.is_project_queued(self.project))

    def test_is_project_queued_when_project_is_not_queued(self):
        self.assertFalse(self.service.is_project_queued(self.project))

    def test_add_project_to_queue_when_project_is_allowed(self):
        self.project.is_allowed = True
        self.project.save(update_fields=["is_allowed"])
        self.assertFalse(self.service.add_project_to_queue(self.project))

    def test_add_project_to_queue_when_project_is_in_queue(self):
        ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        self.assertFalse(self.service.add_project_to_queue(self.project))

    @patch("insights.projects.services.indexer_activation.requests.post")
    def test_activate_project_on_indexer_when_project_is_not_allowed(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = None
        mock_post.return_value.raise_for_status.return_value = None

        activation = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        self.service.activate_project_on_indexer(activation)
        self.assertEqual(self.project.is_allowed, True)

        mock_post.assert_called_once_with(
            settings.WEBHOOK_URL,
            json={"project_uuid": str(self.project.uuid)},
            headers={"Authorization": f"Bearer {settings.STATIC_TOKEN}"},
            timeout=60,
        )

    @patch("insights.projects.services.indexer_activation.requests.post")
    def test_activate_project_on_indexer_when_error_is_raised(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Test error")
        )

        activation = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )

        self.service.activate_project_on_indexer(activation)
        activation.refresh_from_db()
        self.assertEqual(activation.status, ProjectIndexerActivationStatus.FAILED)
