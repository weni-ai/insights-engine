import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase

from insights.projects.consumers.project_consumer import (
    OldProjectConsumer,
    WeniEDAProjectConsumer,
    get_inline_agent_switch,
)
from insights.projects.consumers.update_project_consumer import (
    UpdateProjectConsumer,
)


class TestGetInlineAgentSwitch(TestCase):
    def test_returns_true_when_key_is_missing(self):
        self.assertTrue(get_inline_agent_switch({}))

    def test_returns_true_when_value_is_not_bool(self):
        self.assertTrue(get_inline_agent_switch({"inline_agent_switch": "yes"}))

    def test_returns_true_when_value_is_true(self):
        self.assertTrue(get_inline_agent_switch({"inline_agent_switch": True}))

    def test_returns_false_when_value_is_false(self):
        self.assertFalse(get_inline_agent_switch({"inline_agent_switch": False}))


class TestOldProjectConsumer(TestCase):
    def _make_message(self, body: dict) -> MagicMock:
        message = MagicMock()
        message.body = json.dumps(body).encode()
        message.delivery_tag = "test-delivery-tag"
        message.channel = MagicMock()
        return message

    @patch("insights.projects.consumers.project_consumer.ProjectAuthCreationUseCase")
    @patch("insights.projects.consumers.project_consumer.ProjectsUseCase")
    def test_consume_acks_on_success(self, mock_projects_uc, mock_auth_uc):
        project_uuid = str(uuid4())
        org_uuid = str(uuid4())
        mock_project = MagicMock()
        mock_project.uuid = project_uuid
        mock_projects_uc.return_value.create_project.return_value = mock_project

        body = {
            "uuid": project_uuid,
            "name": "Test Project",
            "is_template": False,
            "date_format": "DD/MM/YYYY",
            "timezone": "UTC",
            "vtex_account": None,
            "organization_uuid": org_uuid,
            "authorizations": [{"user_email": "user@example.com", "role": 1}],
        }
        message = self._make_message(body)

        OldProjectConsumer.consume(message)

        mock_projects_uc.return_value.create_project.assert_called_once()
        mock_auth_uc.return_value.bulk_create.assert_called_once_with(
            project=project_uuid,
            authorizations=body["authorizations"],
        )
        message.channel.basic_ack.assert_called_once_with(message.delivery_tag)
        message.channel.basic_reject.assert_not_called()

    @patch("insights.projects.consumers.project_consumer.ProjectAuthCreationUseCase")
    @patch("insights.projects.consumers.project_consumer.ProjectsUseCase")
    @patch("insights.projects.consumers.project_consumer.capture_exception")
    def test_consume_handles_invalid_organization_uuid(
        self, mock_capture, mock_projects_uc, mock_auth_uc
    ):
        project_uuid = str(uuid4())
        mock_project = MagicMock()
        mock_project.uuid = project_uuid
        mock_projects_uc.return_value.create_project.return_value = mock_project

        body = {
            "uuid": project_uuid,
            "name": "Test Project",
            "is_template": False,
            "date_format": "DD/MM/YYYY",
            "timezone": "UTC",
            "organization_uuid": "not-a-valid-uuid",
        }
        message = self._make_message(body)

        OldProjectConsumer.consume(message)

        mock_capture.assert_called_once()
        dto = mock_projects_uc.return_value.create_project.call_args[0][0]
        self.assertIsNone(dto.org_uuid)
        message.channel.basic_ack.assert_called_once_with(message.delivery_tag)

    @patch("insights.projects.consumers.project_consumer.ProjectsUseCase")
    def test_consume_rejects_on_exception(self, mock_projects_uc):
        mock_projects_uc.return_value.create_project.side_effect = RuntimeError(
            "db error"
        )

        body = {
            "uuid": str(uuid4()),
            "name": "Test Project",
            "is_template": False,
        }
        message = self._make_message(body)

        OldProjectConsumer.consume(message)

        message.channel.basic_reject.assert_called_once_with(
            message.delivery_tag, requeue=False
        )
        message.channel.basic_ack.assert_not_called()


class TestWeniEDAProjectConsumer(TestCase):
    def _make_message(self, body: dict) -> MagicMock:
        message = MagicMock()
        message.body = json.dumps(body).encode()
        message.delivery_tag = "test-delivery-tag"
        message.channel = MagicMock()
        return message

    @patch("insights.projects.consumers.project_consumer.ProjectAuthCreationUseCase")
    @patch("insights.projects.consumers.project_consumer.ProjectsUseCase")
    def test_consume_processes_message_and_acks(self, mock_projects_uc, mock_auth_uc):
        project_uuid = str(uuid4())
        org_uuid = str(uuid4())
        mock_project = MagicMock()
        mock_project.uuid = project_uuid
        mock_projects_uc.return_value.create_project.return_value = mock_project

        body = {
            "uuid": project_uuid,
            "name": "Test Project",
            "is_template": False,
            "date_format": "DD/MM/YYYY",
            "timezone": "UTC",
            "organization_uuid": org_uuid,
            "authorizations": [],
        }
        message = self._make_message(body)

        consumer = WeniEDAProjectConsumer()
        consumer.ack = MagicMock()

        consumer.consume(message)

        mock_projects_uc.return_value.create_project.assert_called_once()
        mock_auth_uc.return_value.bulk_create.assert_called_once_with(
            project=project_uuid,
            authorizations=[],
        )
        consumer.ack.assert_called_once()


class TestUpdateProjectConsumer(TestCase):
    def _make_message(self, body: dict) -> MagicMock:
        message = MagicMock()
        message.body = json.dumps(body).encode()
        message.delivery_tag = "test-delivery-tag"
        message.channel = MagicMock()
        return message

    @patch("insights.projects.consumers.update_project_consumer.UpdateProjectUseCase")
    def test_consume_acks_on_success(self, mock_update_uc):
        project_uuid = str(uuid4())
        body = {
            "project_uuid": project_uuid,
            "name": "Updated Name",
            "timezone": "America/Sao_Paulo",
            "date_format": "DD/MM/YYYY",
        }
        message = self._make_message(body)

        UpdateProjectConsumer.consume(message)

        mock_update_uc.return_value.execute.assert_called_once_with(
            project_uuid=project_uuid,
            name="Updated Name",
            timezone="America/Sao_Paulo",
            date_format="DD/MM/YYYY",
        )
        message.channel.basic_ack.assert_called_once_with(message.delivery_tag)
        message.channel.basic_reject.assert_not_called()

    @patch("insights.projects.consumers.update_project_consumer.capture_exception")
    @patch("insights.projects.consumers.update_project_consumer.UpdateProjectUseCase")
    def test_consume_rejects_on_exception(self, mock_update_uc, mock_capture):
        mock_update_uc.return_value.execute.side_effect = RuntimeError("not found")

        body = {
            "project_uuid": str(uuid4()),
            "name": "Updated Name",
        }
        message = self._make_message(body)

        UpdateProjectConsumer.consume(message)

        message.channel.basic_reject.assert_called_once_with(
            message.delivery_tag, requeue=False
        )
        message.channel.basic_ack.assert_not_called()
        mock_capture.assert_called_once()
