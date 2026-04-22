import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from insights.projects.choices import ProjectIndexerActivationStatus
from insights.projects.models import Project, ProjectIndexerActivation
from insights.projects.tasks import activate_indexer


@override_settings(INDEXER_AUTOMATIC_ACTIVATION=True, INDEXER_AUTOMATIC_ACTIVATION_LIMIT=5)
class TestActivateIndexerTask(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            uuid=uuid.uuid4(),
            is_allowed=False,
        )

    @override_settings(INDEXER_AUTOMATIC_ACTIVATION=False)
    def test_does_nothing_when_automatic_activation_is_disabled(self):
        ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            activate_indexer()
            mock_service_cls.assert_not_called()

    def test_does_nothing_when_no_pending_activations(self):
        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            activate_indexer()
            mock_service_cls.assert_not_called()

    def test_picks_up_pending_activations(self):
        activation = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            activate_indexer()

            mock_service.activate_project_on_indexer.assert_called_once()
            called_activation = mock_service.activate_project_on_indexer.call_args[0][0]
            self.assertEqual(called_activation.pk, activation.pk)

    def test_picks_up_failed_activations(self):
        activation = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.FAILED,
        )
        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            activate_indexer()

            mock_service.activate_project_on_indexer.assert_called_once()
            called_activation = mock_service.activate_project_on_indexer.call_args[0][0]
            self.assertEqual(called_activation.pk, activation.pk)

    def test_ignores_success_activations(self):
        ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.SUCCESS,
        )
        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            activate_indexer()
            mock_service_cls.assert_not_called()

    def test_processes_both_pending_and_failed_activations(self):
        project_2 = Project.objects.create(uuid=uuid.uuid4(), is_allowed=False)

        pending = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        failed = ProjectIndexerActivation.objects.create(
            project=project_2,
            status=ProjectIndexerActivationStatus.FAILED,
        )

        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            activate_indexer()

            self.assertEqual(mock_service.activate_project_on_indexer.call_count, 2)

            called_pks = [
                call[0][0].pk
                for call in mock_service.activate_project_on_indexer.call_args_list
            ]
            self.assertIn(pending.pk, called_pks)
            self.assertIn(failed.pk, called_pks)

    def test_processes_activations_ordered_by_created_on(self):
        project_2 = Project.objects.create(uuid=uuid.uuid4(), is_allowed=False)

        older = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.FAILED,
        )
        newer = ProjectIndexerActivation.objects.create(
            project=project_2,
            status=ProjectIndexerActivationStatus.PENDING,
        )

        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            activate_indexer()

            calls = mock_service.activate_project_on_indexer.call_args_list
            self.assertEqual(calls[0][0][0].pk, older.pk)
            self.assertEqual(calls[1][0][0].pk, newer.pk)

    @patch("insights.projects.tasks.LIMIT", 1)
    def test_respects_activation_limit(self):
        project_2 = Project.objects.create(uuid=uuid.uuid4(), is_allowed=False)

        ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )
        ProjectIndexerActivation.objects.create(
            project=project_2,
            status=ProjectIndexerActivationStatus.FAILED,
        )

        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service

            activate_indexer()

            self.assertEqual(mock_service.activate_project_on_indexer.call_count, 1)

    def test_marks_activation_as_failed_on_exception(self):
        activation = ProjectIndexerActivation.objects.create(
            project=self.project,
            status=ProjectIndexerActivationStatus.PENDING,
        )

        with patch(
            "insights.projects.tasks.ProjectIndexerActivationService"
        ) as mock_service_cls:
            mock_service = MagicMock()
            mock_service.activate_project_on_indexer.side_effect = Exception("boom")
            mock_service_cls.return_value = mock_service

            activate_indexer()

            activation.refresh_from_db()
            self.assertEqual(activation.status, ProjectIndexerActivationStatus.FAILED)
