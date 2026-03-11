from unittest.mock import patch
import responses

from django.conf import settings
from django.test import TestCase, override_settings

from insights.sources.integrations.clients import NexusConversationsAPIClient


@override_settings(NEXUS_CONVERSATIONS_API_BASE_URL="https://conversations.weni.ai")
@override_settings(NEXUS_BASE_URL="https://nexus.weni.ai")
class TestNexusConversationsAPIClient(TestCase):
    def setUp(self):
        self.client = NexusConversationsAPIClient()

    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_use_nexus_conversations_api_when_feature_flag_is_on(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = True

        self.assertTrue(self.client.use_nexus_conversations_api)
        mock_is_feature_active_for_attributes.assert_called_once()

    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_use_nexus_conversations_api_when_feature_flag_is_off(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        self.assertFalse(self.client.use_nexus_conversations_api)
        mock_is_feature_active_for_attributes.assert_called_once()

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_use_nexus_conversations_api_when_force_is_true(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        self.assertTrue(self.client.use_nexus_conversations_api)
        mock_is_feature_active_for_attributes.assert_not_called()

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_base_url_when_use_nexus_conversations_api_is_true(self):
        url = self.client.base_url
        self.assertEqual(url, settings.NEXUS_CONVERSATIONS_API_BASE_URL)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_base_url_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        url = self.client.base_url
        self.assertEqual(url, settings.NEXUS_BASE_URL)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_topics_path_prefix_when_use_nexus_conversations_api_is_true(self):
        path = self.client.topics_path_prefix
        self.assertEqual(path, "api/v1/projects/")

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_topics_path_prefix_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        path = self.client.topics_path_prefix
        self.assertEqual(path, "")

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_headers_when_use_nexus_conversations_api_is_true(self):
        headers = self.client.headers
        self.assertEqual(
            headers,
            {
                "Authorization": f"Bearer {settings.NEXUS_CONVERSATIONS_API_TOKEN}",
            },
        )

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_headers_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        headers = self.client.headers
        self.assertEqual(
            headers,
            {
                "Authorization": f"Bearer {settings.NEXUS_API_TOKEN}",
            },
        )

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_get_topics_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/",
                json=[],
                status=200,
            )
            response = self.client.get_topics(project_uuid="123")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_get_topics_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_BASE_URL}/123/topics/",
                json=[],
                status=200,
            )

            response = self.client.get_topics(project_uuid="123")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_get_subtopics_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/456/subtopics/",
                json=[],
                status=200,
            )
            response = self.client.get_subtopics(project_uuid="123", topic_uuid="456")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_get_subtopics_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{settings.NEXUS_BASE_URL}/123/topics/456/subtopics/",
                json=[],
                status=200,
            )

            response = self.client.get_subtopics(project_uuid="123", topic_uuid="456")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_create_topic_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/",
                json={},
                status=201,
            )
            response = self.client.create_topic(
                project_uuid="123", name="Topic", description="Desc"
            )
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_create_topic_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{settings.NEXUS_BASE_URL}/123/topics/",
                json={},
                status=201,
            )

            response = self.client.create_topic(
                project_uuid="123", name="Topic", description="Desc"
            )
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_create_subtopic_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/456/subtopics/",
                json={},
                status=201,
            )
            response = self.client.create_subtopic(
                project_uuid="123",
                topic_uuid="456",
                name="Subtopic",
                description="Desc",
            )
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_create_subtopic_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{settings.NEXUS_BASE_URL}/123/topics/456/subtopics/",
                json={},
                status=201,
            )

            response = self.client.create_subtopic(
                project_uuid="123",
                topic_uuid="456",
                name="Subtopic",
                description="Desc",
            )
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_delete_topic_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/456/",
                status=204,
            )
            response = self.client.delete_topic(project_uuid="123", topic_uuid="456")
            self.assertEqual(response.status_code, 204)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_delete_topic_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                f"{settings.NEXUS_BASE_URL}/123/topics/456/",
                status=204,
            )

            response = self.client.delete_topic(project_uuid="123", topic_uuid="456")
            self.assertEqual(response.status_code, 204)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=True)
    def test_delete_subtopic_when_use_nexus_conversations_api_is_true(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/456/subtopics/789/",
                status=204,
            )
            response = self.client.delete_subtopic(
                project_uuid="123", topic_uuid="456", subtopic_uuid="789"
            )
            self.assertEqual(response.status_code, 204)

            self.assertEqual(len(rsps.calls), 1)

    @override_settings(FORCE_USE_NEXUS_CONVERSATIONS_API=False)
    @patch("insights.sources.integrations.clients.is_feature_active_for_attributes")
    def test_delete_subtopic_when_use_nexus_conversations_api_is_false(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                f"{settings.NEXUS_BASE_URL}/123/topics/456/subtopics/789/",
                status=204,
            )

            response = self.client.delete_subtopic(
                project_uuid="123", topic_uuid="456", subtopic_uuid="789"
            )
            self.assertEqual(response.status_code, 204)

            self.assertEqual(len(rsps.calls), 1)
