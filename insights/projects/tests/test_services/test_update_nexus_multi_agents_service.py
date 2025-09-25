from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings


from insights.projects.services.update_nexus_multi_agents_status import (
    UpdateNexusMultiAgentsStatusService,
)
from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.sources.tests.mock import MockCacheClient
from insights.projects.tests.mock import MockIndexerActivationService
from insights.projects.models import Project
from insights.projects.tests.test_services.test_indexer_activation_service import (
    PROJECT_UUID,
)


class TestUpdateNexusMultiAgentsService(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            uuid=PROJECT_UUID,
            is_allowed=False,
        )
        self.service = UpdateNexusMultiAgentsStatusService(
            nexus_client=MockNexusClient(),
            cache_client=MockCacheClient(),
            indexer_activation_service=MockIndexerActivationService(),
        )

    @patch.object(MockNexusClient, "get_project_multi_agents_status")
    @patch.object(MockCacheClient, "get")
    def test_update_when_multi_agents_are_false(self, mock_cache_get, mock_get_status):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"multi_agents": False}
        mock_get_status.return_value = mock_response

        mock_cache_get.return_value = None

        self.service.update(self.project)
        self.project.refresh_from_db(fields=["is_nexus_multi_agents_active"])
        self.assertFalse(self.project.is_nexus_multi_agents_active)
        mock_cache_get.assert_called_once_with(
            f"nexus_multi_agents_status:{self.project.uuid}"
        )

    @override_settings(CONVERSATIONS_DASHBOARD_REQUIRES_INDEXER_ACTIVATION=True)
    @patch.object(MockNexusClient, "get_project_multi_agents_status")
    @patch.object(MockCacheClient, "get")
    @patch.object(MockCacheClient, "set")
    def test_update_when_multi_agents_are_true(
        self, mock_cache_set, mock_cache_get, mock_get_status
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"multi_agents": True}
        mock_get_status.return_value = mock_response

        mock_cache_get.return_value = None
        mock_cache_set.return_value = True

        # Mock the instance methods
        self.service.indexer_activation_service.is_project_active_on_indexer = (
            MagicMock(return_value=False)
        )
        self.service.indexer_activation_service.is_project_queued = MagicMock(
            return_value=False
        )
        self.service.indexer_activation_service.add_project_to_queue = MagicMock(
            return_value=True
        )

        self.service.update(self.project)
        self.project.refresh_from_db(fields=["is_nexus_multi_agents_active"])
        self.assertTrue(self.project.is_nexus_multi_agents_active)

        self.service.indexer_activation_service.is_project_active_on_indexer.assert_called_once_with(
            self.project
        )
        self.service.indexer_activation_service.is_project_queued.assert_called_once_with(
            self.project
        )
        self.service.indexer_activation_service.add_project_to_queue.assert_called_once_with(
            self.project
        )

        mock_cache_get.assert_called_once_with(
            f"nexus_multi_agents_status:{self.project.uuid}"
        )
        mock_cache_set.assert_called_once_with(
            f"nexus_multi_agents_status:{self.project.uuid}",
            "True",
            10,
        )

    @override_settings(CONVERSATIONS_DASHBOARD_REQUIRES_INDEXER_ACTIVATION=True)
    @patch.object(MockNexusClient, "get_project_multi_agents_status")
    def test_update_when_multi_agents_are_true_and_project_is_active_on_indexer(
        self, mock_get_status
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"multi_agents": True}
        mock_get_status.return_value = mock_response

        self.service.indexer_activation_service.is_project_active_on_indexer = (
            MagicMock(return_value=True)
        )
        self.service.update(self.project)
        self.project.refresh_from_db(fields=["is_nexus_multi_agents_active"])
        self.assertTrue(self.project.is_nexus_multi_agents_active)

        self.service.indexer_activation_service.is_project_active_on_indexer.assert_called_once_with(
            self.project
        )
        self.service.indexer_activation_service.is_project_queued.assert_not_called()
        self.service.indexer_activation_service.add_project_to_queue.assert_not_called()

    @override_settings(CONVERSATIONS_DASHBOARD_REQUIRES_INDEXER_ACTIVATION=True)
    @patch.object(MockNexusClient, "get_project_multi_agents_status")
    def test_update_when_multi_agents_are_true_and_project_is_queued(
        self, mock_get_status
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"multi_agents": True}
        mock_get_status.return_value = mock_response

        self.service.indexer_activation_service.is_project_active_on_indexer = (
            MagicMock(return_value=False)
        )
        self.service.indexer_activation_service.is_project_queued = MagicMock(
            return_value=True
        )
        self.service.update(self.project)
        self.project.refresh_from_db(fields=["is_nexus_multi_agents_active"])
        self.assertTrue(self.project.is_nexus_multi_agents_active)

        self.service.indexer_activation_service.is_project_active_on_indexer.assert_called_once_with(
            self.project
        )
        self.service.indexer_activation_service.is_project_queued.assert_called_once_with(
            self.project
        )
        self.service.indexer_activation_service.add_project_to_queue.assert_not_called()

    @patch.object(MockCacheClient, "get")
    def test_update_when_multi_agents_result_is_cached(self, mock_cache_get):
        mock_cache_get.return_value = True
        self.service.update(self.project)
        self.project.refresh_from_db(fields=["is_nexus_multi_agents_active"])
        self.assertTrue(self.project.is_nexus_multi_agents_active)

        mock_cache_get.assert_called_once_with(
            f"nexus_multi_agents_status:{self.project.uuid}"
        )
