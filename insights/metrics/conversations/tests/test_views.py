from unittest.mock import patch
import uuid

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
)
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
    NPS_METRICS_MOCK_DATA,
)
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_totals(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/totals/"

        return self.client.get(url, query_params)

    def get_timeseries(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/timeseries/"

        return self.client.get(url, query_params)

    def get_subjects_metrics(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/subjects/"

        return self.client.get(url, query_params)

    def get_queues_metrics(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/queues/"

        return self.client.get(url, query_params)

    def get_subjects_distribution(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/subjects-distribution/"

        return self.client.get(url, query_params)

    def get_nps(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/nps/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_totals_when_not_authenticated(self):
        response = self.get_totals({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_timeseries_when_unauthenticated(self) -> None:
        response = self.get_timeseries({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_subjects_metrics_when_unauthenticated(self):
        response = self.get_subjects_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_queue_metrics_when_unauthenticated(self):
        response = self.get_queues_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_subjects_distribution_when_unauthenticated(self):
        response = self.get_subjects_distribution({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_nps_when_unauthenticated(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(self.user)

    def test_cannot_get_totals_without_permission(self):
        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_totals_without_project_uuid(self):
        response = self.get_totals({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_totals_without_required_query_params(self):
        response = self.get_totals({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_totals"
    )
    def test_get_totals(self, mock_get_totals):
        mock_get_totals.return_value = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
        )

        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_conversations"]["value"], 100)
        self.assertEqual(response.data["total_conversations"]["percentage"], 100)
        self.assertEqual(response.data["resolved"]["value"], 60)
        self.assertEqual(response.data["resolved"]["percentage"], 60)
        self.assertEqual(response.data["unresolved"]["value"], 40)
        self.assertEqual(response.data["unresolved"]["percentage"], 40)

    def test_cannot_get_timeseries_without_permission(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.HOUR,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_timeseries_without_project_uuid(self) -> None:
        response = self.get_timeseries(
            {
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.HOUR,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_timeseries_without_required_query_params(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["unit"][0].code, "required")

    @with_project_auth
    def test_cannot_get_timeseries_with_invalid_unit(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": "CENTURY",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["unit"][0].code, "invalid_choice")

    @with_project_auth
    def test_cannot_get_timeseries_with_invalid_start_date(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-02-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.HOUR,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["start_date"][0].code, "start_date_after_end_date"
        )

    @with_project_auth
    def test_get_timeseries_for_hour_unit(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.HOUR,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unit"], ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            response.data["total"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["total"],
        )
        self.assertEqual(
            response.data["by_human"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["by_human"],
        )

    @with_project_auth
    def test_get_timeseries_for_day_unit(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.DAY,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unit"], ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            response.data["total"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "total"
            ],
        )
        self.assertEqual(
            response.data["by_human"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "by_human"
            ],
        )

    @with_project_auth
    def test_get_timeseries_for_month_unit(self) -> None:
        response = self.get_timeseries(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "unit": ConversationsTimeseriesUnit.MONTH,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unit"], ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            response.data["total"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["total"],
        )
        self.assertEqual(
            response.data["by_human"],
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["by_human"],
        )

    def test_cannot_get_subjects_metrics_without_permission(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_subjects_metrics_without_project_uuid(self):
        response = self.get_subjects_metrics(
            {
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_subjects_metrics_without_required_query_params(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_subjects_metrics(self):
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get(
            "subjects", []
        )

        self.assertEqual(response.data["has_more"], False)
        self.assertEqual(len(response.data["subjects"]), len(mock_subjects_data))

        for i, subject in enumerate(response.data["subjects"]):
            self.assertEqual(subject["name"], mock_subjects_data[i]["name"])
            self.assertEqual(subject["percentage"], mock_subjects_data[i]["percentage"])

    @with_project_auth
    def test_get_subjects_metrics_with_limit(self):
        mock_subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get(
            "subjects", []
        )
        response = self.get_subjects_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationsSubjectsType.GENERAL,
                "limit": len(mock_subjects_data) - 1,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["has_more"], True)
        self.assertEqual(len(response.data["subjects"]), len(mock_subjects_data) - 1)

        for i, subject in enumerate(response.data["subjects"]):
            self.assertEqual(subject["name"], mock_subjects_data[i]["name"])
            self.assertEqual(subject["percentage"], mock_subjects_data[i]["percentage"])

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

    def test_cannot_get_subjects_distribution_without_project_uuid(self):
        response = self.get_subjects_distribution({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["project_uuid"][0].code,
            "required",
        )

    def test_cannot_get_subjects_distribution_without_permission(self):
        response = self.get_subjects_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_subjects_distribution_without_required_fields(self):
        response = self.get_subjects_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["start_date"][0].code,
            "required",
        )
        self.assertEqual(
            response.data["end_date"][0].code,
            "required",
        )

    @with_project_auth
    def test_get_subjects_distribution(self):
        response = self.get_subjects_distribution(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for group_data, group in zip(
            response.data["groups"],
            CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA.get("groups"),
        ):
            self.assertEqual(group_data["name"], group["name"])
            self.assertEqual(group_data["percentage"], group["percentage"])
            for subject_data, subject in zip(group_data["subjects"], group["subjects"]):
                self.assertEqual(subject_data["name"], subject["name"])
                self.assertEqual(subject_data["percentage"], subject["percentage"])

    def test_cannot_get_nps_without_project_uuid(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_nps_without_permission(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_nps_without_required_query_params(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_nps(self):
        response = self.get_nps(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": NPSType.HUMAN,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], NPS_METRICS_MOCK_DATA["score"])
        self.assertEqual(
            response.data["total_responses"], NPS_METRICS_MOCK_DATA["total_responses"]
        )
        self.assertEqual(response.data["promoters"], NPS_METRICS_MOCK_DATA["promoters"])
        self.assertEqual(
            response.data["detractors"], NPS_METRICS_MOCK_DATA["detractors"]
        )
        self.assertEqual(response.data["passives"], NPS_METRICS_MOCK_DATA["passives"])
