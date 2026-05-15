import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class TestCheckDashboardsMarketingMessagesStatusForProject(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.task_path = (
            "insights.metrics.meta.tasks"
            ".check_marketing_messages_status"
        )

    def _create_dashboard(self, config=None):
        return Dashboard.objects.create(
            project=self.project,
            name="Test Dashboard",
            description="desc",
            config=config,
        )

    def _call_task(self):
        from insights.metrics.meta.tasks import (
            check_dashboards_marketing_messages_status_for_project,
        )

        check_dashboards_marketing_messages_status_for_project(
            self.project.uuid,
        )

    def test_no_whatsapp_dashboards(self):
        self._create_dashboard(config={"is_whatsapp_integration": False})

        with patch(self.task_path) as mock_task:
            self._call_task()
            mock_task.apply_async.assert_not_called()

    def test_skips_recently_checked_dashboard(self):
        recent = (timezone.now() - timedelta(minutes=5)).isoformat()
        self._create_dashboard(
            config={
                "is_whatsapp_integration": True,
                "marketing_messages_status_last_checked_at": recent,
            },
        )

        with patch(self.task_path) as mock_task:
            self._call_task()
            mock_task.apply_async.assert_not_called()

    def test_dispatches_for_old_check(self):
        old = (timezone.now() - timedelta(minutes=20)).isoformat()
        dashboard = self._create_dashboard(
            config={
                "is_whatsapp_integration": True,
                "marketing_messages_status_last_checked_at": old,
            },
        )

        with patch(self.task_path) as mock_task:
            self._call_task()
            mock_task.apply_async.assert_called_once()
            args = mock_task.apply_async.call_args
            self.assertEqual(args.kwargs["args"], [dashboard.uuid])

    def test_dispatches_when_never_checked(self):
        dashboard = self._create_dashboard(
            config={"is_whatsapp_integration": True},
        )

        with patch(self.task_path) as mock_task:
            self._call_task()
            mock_task.apply_async.assert_called_once()
            args = mock_task.apply_async.call_args
            self.assertEqual(args.kwargs["args"], [dashboard.uuid])

    @patch("insights.metrics.meta.tasks.capture_exception")
    def test_captures_exception_for_invalid_datetime(self, mock_capture):
        mock_capture.return_value = "event-123"
        self._create_dashboard(
            config={
                "is_whatsapp_integration": True,
                "marketing_messages_status_last_checked_at": "not-a-date",
            },
        )

        with patch(self.task_path) as mock_task:
            self._call_task()
            mock_capture.assert_called_once()
            mock_task.apply_async.assert_not_called()


class TestCheckMarketingMessagesStatus(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def _call_task(self, dashboard_uuid):
        from insights.metrics.meta.tasks import check_marketing_messages_status

        check_marketing_messages_status(dashboard_uuid)

    @patch("insights.metrics.meta.tasks.capture_exception")
    def test_nonexistent_dashboard(self, mock_capture):
        mock_capture.return_value = "event-456"
        missing_uuid = uuid.uuid4()

        self._call_task(missing_uuid)

        mock_capture.assert_called_once()
        exc = mock_capture.call_args[0][0]
        self.assertIsInstance(exc, Dashboard.DoesNotExist)

    def test_not_whatsapp_integration(self):
        dashboard = Dashboard.objects.create(
            project=self.project,
            name="Non-WA",
            description="desc",
            config={"is_whatsapp_integration": False},
        )

        with patch(
            "insights.metrics.meta.tasks.MetaMessageTemplatesService"
        ) as mock_svc_cls:
            self._call_task(dashboard.uuid)
            mock_svc_cls.assert_not_called()

    def test_missing_waba_id(self):
        dashboard = Dashboard.objects.create(
            project=self.project,
            name="WA no waba",
            description="desc",
            config={"is_whatsapp_integration": True},
        )

        with patch(
            "insights.metrics.meta.tasks.MetaMessageTemplatesService"
        ) as mock_svc_cls:
            self._call_task(dashboard.uuid)
            mock_svc_cls.assert_not_called()

    @patch("insights.metrics.meta.tasks.MetaMessageTemplatesService")
    def test_successful_check_updates_config(self, mock_svc_cls):
        mock_service = MagicMock()
        mock_service.check_marketing_messages_status.return_value = True
        mock_svc_cls.return_value = mock_service

        dashboard = Dashboard.objects.create(
            project=self.project,
            name="WA Dashboard",
            description="desc",
            config={
                "is_whatsapp_integration": True,
                "waba_id": "123456",
            },
        )

        self._call_task(dashboard.uuid)

        mock_service.check_marketing_messages_status.assert_called_once_with(
            waba_id="123456",
        )

        dashboard.refresh_from_db()
        self.assertTrue(dashboard.config["is_mm_lite_active"])
        self.assertIn(
            "marketing_messages_status_last_checked_at",
            dashboard.config,
        )
