import responses

from django.conf import settings
from django.test import TestCase, override_settings

from insights.sources.integrations.clients import NexusConversationsAPIClient


@override_settings(NEXUS_CONVERSATIONS_API_BASE_URL="https://conversations.weni.ai")
class TestNexusConversationsAPIClient(TestCase):
    def setUp(self):
        self.client = NexusConversationsAPIClient()

    def test_base_url(self):
        self.assertEqual(
            self.client.base_url, settings.NEXUS_CONVERSATIONS_API_BASE_URL
        )

    def test_headers(self):
        headers = self.client.headers
        self.assertEqual(
            headers,
            {
                "Authorization": f"Bearer {settings.NEXUS_CONVERSATIONS_API_TOKEN}",
            },
        )

    def test_get_topics(self):
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

    def test_get_subtopics(self):
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

    def test_create_topic(self):
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

    def test_create_subtopic(self):
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

    def test_delete_topic(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.DELETE,
                f"{settings.NEXUS_CONVERSATIONS_API_BASE_URL}/api/v1/projects/123/topics/456/",
                status=204,
            )
            response = self.client.delete_topic(project_uuid="123", topic_uuid="456")
            self.assertEqual(response.status_code, 204)

            self.assertEqual(len(rsps.calls), 1)

    def test_delete_subtopic(self):
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
