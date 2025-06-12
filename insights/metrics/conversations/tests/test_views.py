from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
)
from insights.projects.models import Project


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_totals(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/totals/"

        return self.client.get(url, query_params)

    def get_timeseries(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/timeseries/"

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
    def test_get_totals(self):
        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["total"],
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
            + CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )
        self.assertEqual(
            response.data["by_ai"]["value"],
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"],
        )
        self.assertEqual(
            response.data["by_ai"]["percentage"],
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
            / response.data["total"]
            * 100,
        )
        self.assertEqual(
            response.data["by_human"]["value"],
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )
        self.assertEqual(
            response.data["by_human"]["percentage"],
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"]
            / response.data["total"]
            * 100,
        )

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
