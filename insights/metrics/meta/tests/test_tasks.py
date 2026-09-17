import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from insights.dashboards.models import Dashboard
from insights.projects.models import Project
from insights.widgets.models import Widget


class TestCheckDashboardsMarketingMessagesStatusForProject(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.task_path = (
            "insights.metrics.meta.tasks" ".check_marketing_messages_status"
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


class TestMoveFavoriteTemplatesTask(TestCase):
    @patch(
        "insights.metrics.meta.usecases.move_favorite_templates."
        "MoveFavoriteTemplatesUseCase.execute"
    )
    def test_calls_use_case(self, mock_execute):
        from insights.metrics.meta.tasks import move_favorite_templates

        mock_execute.return_value = 2
        old_uuid = uuid.uuid4()
        new_uuid = uuid.uuid4()

        move_favorite_templates(old_uuid, new_uuid)

        mock_execute.assert_called_once_with(
            old_dashboard_uuid=old_uuid,
            new_dashboard_uuid=new_uuid,
        )

    @patch("insights.metrics.meta.tasks.capture_exception")
    @patch(
        "insights.metrics.meta.usecases.move_favorite_templates."
        "MoveFavoriteTemplatesUseCase.execute"
    )
    def test_captures_and_reraises_exception_for_retry(
        self, mock_execute, mock_capture
    ):
        from celery.exceptions import Retry

        from insights.metrics.meta.tasks import move_favorite_templates

        mock_execute.side_effect = RuntimeError("boom")
        mock_capture.return_value = "event-789"

        with self.assertRaises((Retry, RuntimeError)):
            move_favorite_templates(uuid.uuid4(), uuid.uuid4())

        mock_capture.assert_called_once()


class TestMigrateWidgetsWabaConfig(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.other_project = Project.objects.create(name="Other Project")
        self.old_waba_id = "old_waba_123"
        self.new_waba_id = "new_waba_456"
        self.old_template_id = "old_template_1"
        self.new_template_id = "new_template_1"
        self.dashboard = Dashboard.objects.create(
            project=self.project,
            name="Custom Dashboard",
        )
        self.other_dashboard = Dashboard.objects.create(
            project=self.other_project,
            name="Other Dashboard",
        )

    def _create_vtex_widget(self, *, dashboard, waba_id, template_id, extra_config=None):
        config = {
            "operation": "list",
            "filter": {
                "waba_id": waba_id,
                "template_id": template_id,
                "utm_source": "weniabandonedcart",
            },
        }
        if extra_config:
            config.update(extra_config)
        return Widget.objects.create(
            dashboard=dashboard,
            name="Carrinho abandonado",
            type="graph_column",
            source="vtex_conversions",
            position={},
            config=config,
        )

    def _call_task(self):
        from insights.metrics.meta.tasks import migrate_widgets_waba_config

        migrate_widgets_waba_config(
            project_uuid=str(self.project.uuid),
            old_waba_id=self.old_waba_id,
            new_waba_id=self.new_waba_id,
        )

    @patch("insights.metrics.meta.tasks.MetaGraphAPIClient")
    def test_updates_waba_and_template_id_preserving_other_config(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_template_preview.return_value = {
            "name": "weni_abandoned_cart",
            "id": self.old_template_id,
        }
        mock_client.get_templates_list.return_value = {
            "data": [{"id": self.new_template_id, "name": "weni_abandoned_cart"}]
        }

        widget = self._create_vtex_widget(
            dashboard=self.dashboard,
            waba_id=self.old_waba_id,
            template_id=self.old_template_id,
            extra_config={"op_field": "sent", "custom_flag": True},
        )

        self._call_task()

        widget.refresh_from_db()
        self.assertEqual(widget.config["filter"]["waba_id"], self.new_waba_id)
        self.assertEqual(widget.config["filter"]["template_id"], self.new_template_id)
        self.assertEqual(
            widget.config["filter"]["utm_source"], "weniabandonedcart"
        )
        self.assertEqual(widget.config["operation"], "list")
        self.assertEqual(widget.config["op_field"], "sent")
        self.assertTrue(widget.config["custom_flag"])

    @patch("insights.metrics.meta.tasks.MetaGraphAPIClient")
    def test_keeps_template_id_when_equivalent_not_found(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_template_preview.return_value = {
            "name": "weni_abandoned_cart",
            "id": self.old_template_id,
        }
        mock_client.get_templates_list.return_value = {"data": []}

        widget = self._create_vtex_widget(
            dashboard=self.dashboard,
            waba_id=self.old_waba_id,
            template_id=self.old_template_id,
        )

        self._call_task()

        widget.refresh_from_db()
        self.assertEqual(widget.config["filter"]["waba_id"], self.new_waba_id)
        self.assertEqual(widget.config["filter"]["template_id"], self.old_template_id)
        self.assertEqual(
            widget.config["filter"]["utm_source"], "weniabandonedcart"
        )

    @patch("insights.metrics.meta.tasks.MetaGraphAPIClient")
    def test_ignores_widgets_from_other_project_or_waba(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        matching = self._create_vtex_widget(
            dashboard=self.dashboard,
            waba_id=self.old_waba_id,
            template_id=self.old_template_id,
        )
        other_waba = self._create_vtex_widget(
            dashboard=self.dashboard,
            waba_id="another_waba",
            template_id="tpl_other",
        )
        other_project = self._create_vtex_widget(
            dashboard=self.other_dashboard,
            waba_id=self.old_waba_id,
            template_id=self.old_template_id,
        )

        mock_client.get_template_preview.return_value = {
            "name": "weni_abandoned_cart",
            "id": self.old_template_id,
        }
        mock_client.get_templates_list.return_value = {
            "data": [{"id": self.new_template_id, "name": "weni_abandoned_cart"}]
        }

        self._call_task()

        matching.refresh_from_db()
        other_waba.refresh_from_db()
        other_project.refresh_from_db()

        self.assertEqual(matching.config["filter"]["waba_id"], self.new_waba_id)
        self.assertEqual(other_waba.config["filter"]["waba_id"], "another_waba")
        self.assertEqual(
            other_project.config["filter"]["waba_id"], self.old_waba_id
        )

    @patch("insights.metrics.meta.tasks.MetaGraphAPIClient")
    def test_is_idempotent(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_template_preview.return_value = {
            "name": "weni_abandoned_cart",
            "id": self.old_template_id,
        }
        mock_client.get_templates_list.return_value = {
            "data": [{"id": self.new_template_id, "name": "weni_abandoned_cart"}]
        }

        widget = self._create_vtex_widget(
            dashboard=self.dashboard,
            waba_id=self.old_waba_id,
            template_id=self.old_template_id,
        )

        self._call_task()
        self._call_task()

        widget.refresh_from_db()
        self.assertEqual(widget.config["filter"]["waba_id"], self.new_waba_id)
        self.assertEqual(widget.config["filter"]["template_id"], self.new_template_id)
        self.assertEqual(mock_client.get_template_preview.call_count, 1)

    @patch("insights.metrics.meta.tasks.capture_exception")
    def test_nonexistent_project(self, mock_capture):
        from insights.metrics.meta.tasks import migrate_widgets_waba_config

        mock_capture.return_value = "event-789"
        migrate_widgets_waba_config(
            project_uuid=str(uuid.uuid4()),
            old_waba_id=self.old_waba_id,
            new_waba_id=self.new_waba_id,
        )

        mock_capture.assert_called_once()
        self.assertIsInstance(mock_capture.call_args[0][0], Project.DoesNotExist)
