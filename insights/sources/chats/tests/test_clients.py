from unittest.mock import patch
import uuid

from django.test import TestCase

from unittest.mock import MagicMock
from insights.internals.base import InternalAuthentication
from insights.sources.chats.clients import ChatsRESTClient


@patch.object(
    InternalAuthentication,
    "headers",
    new_callable=lambda: {
        "Content-Type": "application/json; charset: utf-8",
        "Authorization": "Bearer mock-token",
    },
)
class ChatsRESTClientTestCase(TestCase):
    def setUp(self):
        self.client = ChatsRESTClient()

    @patch("insights.sources.chats.clients.request_with_retry")
    def test_get_project(self, mock_request_with_retry, mock_headers):
        project_uuid = str(uuid.uuid4())
        expected_response = {
            "uuid": project_uuid,
            "name": "Test Project",
            "date_format": "D",
            "timezone": "America/Fortaleza",
            "ticketer": {},
            "queue": {},
        }

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        mock_request_with_retry.return_value = mock_response

        project = self.client.get_project(project_uuid=project_uuid)

        self.assertEqual(project, expected_response)

        mock_request_with_retry.assert_called_once_with(
            url=f"/internal/project/{project_uuid}",
            headers={
                "Content-Type": "application/json; charset: utf-8",
                "Authorization": "Bearer mock-token",
            },
            params={},
            method="GET",
            timeout=60,
            max_retries=3,
        )
