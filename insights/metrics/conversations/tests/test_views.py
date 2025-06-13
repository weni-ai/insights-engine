from unittest.mock import patch
import uuid

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_queues_metrics(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/queues/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_queue_metrics_when_unauthenticated(self):
        response = self.get_queues_metrics({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

    def test_cannot_get_queue_metrics_without_permission(self):
        response = self.get_queues_metrics(
            {
                "project_uuid": str(self.project.uuid),
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_queue_metrics_without_required_query_params(self):
        response = self.get_queues_metrics({"project_uuid": str(self.project.uuid)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    @with_project_auth
    def test_get_queue_metrics(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]

        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        response = self.get_queues_metrics(
            {
                "project_uuid": str(self.project.uuid),
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("queues", response.data)
        self.assertIn("has_more", response.data)
        self.assertEqual(
            response.data["queues"],
            [
                {
                    "name": "Test Queue",
                    "percentage": 33.33,
                },
                {
                    "name": "Test Queue 2",
                    "percentage": 66.67,
                },
            ],
        )
        self.assertEqual(response.data["has_more"], False)

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    @with_project_auth
    def test_get_queue_metrics_with_limit(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]

        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        response = self.get_queues_metrics(
            {
                "project_uuid": str(self.project.uuid),
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "limit": 1,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("queues", response.data)
        self.assertIn("has_more", response.data)
        self.assertEqual(
            response.data["queues"],
            [
                {
                    "name": "Test Queue",
                    "percentage": 33.33,
                },
            ],
        )
        self.assertEqual(response.data["has_more"], True)
