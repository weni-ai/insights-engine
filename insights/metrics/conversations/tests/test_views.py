from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase


class BaseTestConversationsMetricsViewSet(APITestCase):
    def get_totals(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/totals/"

        return self.client.get(url, query_params)


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_totals_when_not_authenticated(self):
        response = self.get_totals({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    pass
