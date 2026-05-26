import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase

from insights.projects.models import Project
from insights.projects.tasks import (
    check_nexus_multi_agents_status,
    handle_project_created_with_inline_agent_switch,
)


class TestCheckNexusMultiAgentsStatus(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            uuid=uuid.uuid4(),
            is_allowed=False,
        )

    def test_returns_early_when_multi_agents_already_active(self):
        self.project.is_nexus_multi_agents_active = True
        self.project.save(update_fields=["is_nexus_multi_agents_active"])

        with patch(
            "insights.projects.tasks.UpdateNexusMultiAgentsStatusService"
        ) as mock_service_cls:
            check_nexus_multi_agents_status(self.project.uuid)
            mock_service_cls.assert_not_called()

    @patch("insights.projects.tasks.ProjectIndexerActivationService")
    @patch("insights.projects.tasks.CacheClient")
    @patch("insights.projects.tasks.NexusClient")
    def test_calls_service_update_when_not_active(
        self, mock_nexus_cls, mock_cache_cls, mock_indexer_cls
    ):
        with patch(
            "insights.projects.tasks.UpdateNexusMultiAgentsStatusService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            check_nexus_multi_agents_status(self.project.uuid)

            mock_service_cls.assert_called_once_with(
                nexus_client=mock_nexus_cls.return_value,
                cache_client=mock_cache_cls.return_value,
                indexer_activation_service=mock_indexer_cls.return_value,
            )
            mock_service.update.assert_called_once()
            called_project = mock_service.update.call_args[0][0]
            self.assertEqual(called_project.pk, self.project.pk)


class TestHandleProjectCreatedWithInlineAgentSwitch(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            uuid=uuid.uuid4(),
            is_allowed=False,
        )

    def test_returns_early_when_multi_agents_not_active(self):
        with patch(
            "insights.projects.tasks.UpdateNexusMultiAgentsStatusService"
        ) as mock_service_cls:
            handle_project_created_with_inline_agent_switch(self.project.uuid)
            mock_service_cls.assert_not_called()

    @patch("insights.projects.tasks.create_conversation_dashboard")
    @patch("insights.projects.tasks.ProjectIndexerActivationService")
    @patch("insights.projects.tasks.CacheClient")
    @patch("insights.projects.tasks.NexusClient")
    def test_adds_to_indexer_queue_and_creates_dashboard_when_active(
        self, mock_nexus_cls, mock_cache_cls, mock_indexer_cls, mock_create_dashboard
    ):
        self.project.is_nexus_multi_agents_active = True
        self.project.save(update_fields=["is_nexus_multi_agents_active"])

        with patch(
            "insights.projects.tasks.UpdateNexusMultiAgentsStatusService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            handle_project_created_with_inline_agent_switch(self.project.uuid)

            mock_service.add_project_to_indexer_queue.assert_called_once()
            mock_create_dashboard.delay.assert_called_once_with(self.project.uuid)

    @patch("insights.projects.tasks.create_conversation_dashboard")
    @patch("insights.projects.tasks.ProjectIndexerActivationService")
    @patch("insights.projects.tasks.CacheClient")
    @patch("insights.projects.tasks.NexusClient")
    def test_skips_dashboard_creation_when_dashboard_already_exists(
        self, mock_nexus_cls, mock_cache_cls, mock_indexer_cls, mock_create_dashboard
    ):
        self.project.is_nexus_multi_agents_active = True
        self.project.save(update_fields=["is_nexus_multi_agents_active"])

        with patch("insights.projects.tasks.Dashboard.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True

            with patch(
                "insights.projects.tasks.UpdateNexusMultiAgentsStatusService"
            ) as mock_service_cls:
                mock_service = MagicMock()
                mock_service_cls.return_value = mock_service

                handle_project_created_with_inline_agent_switch(self.project.uuid)

                mock_service.add_project_to_indexer_queue.assert_called_once()
                mock_create_dashboard.delay.assert_not_called()
