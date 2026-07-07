from unittest.mock import patch, MagicMock, PropertyMock
import uuid

from django.test import TestCase

from insights.sources.chats.clients import ChatsRESTClient


class ChatsRESTClientTestCase(TestCase):
    def setUp(self):
        self.project = MagicMock()
        self.project.uuid = uuid.uuid4()

    @patch("insights.sources.chats.clients.request_with_retry")
    @patch.object(
        ChatsRESTClient,
        "headers",
        new_callable=PropertyMock,
        return_value={
            "Content-Type": "application/json; charset: utf-8",
            "Authorization": "Bearer mock-token",
        },
    )
    def test_get_project(self, mock_headers, mock_request_with_retry):
        expected_response = {
            "uuid": str(self.project.uuid),
            "name": "Test Project",
            "date_format": "D",
            "timezone": "America/Fortaleza",
            "ticketer": {},
            "queue": {},
        }

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        mock_request_with_retry.return_value = mock_response

        client = ChatsRESTClient(self.project)
        project = client.get_project()

        self.assertEqual(project, expected_response)

        mock_request_with_retry.assert_called_once_with(
            url=f"/v1/internal/project/{self.project.uuid}/",
            headers={
                "Content-Type": "application/json; charset: utf-8",
                "Authorization": "Bearer mock-token",
            },
            params={},
            method="GET",
            timeout=60,
            max_retries=3,
        )
