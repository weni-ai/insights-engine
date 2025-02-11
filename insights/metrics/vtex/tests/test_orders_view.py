from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from unittest.mock import patch

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


class BaseTestVtexOrdersView(APITestCase):
    base_url = "/v1/metrics/vtex/orders/"

    def get_utm_revenue(self, query_params: dict | None = None) -> Response:
        url = self.base_url + "utm_revenue/"

        return self.client.get(url, query_params)


class TestVtexOrdersViewAsAnonymousUser(BaseTestVtexOrdersView):
    def test_get_utm_revenue_without_project_uuid(self):
        response = self.get_utm_revenue()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestVtexOrdersViewAsAuthenticatedUser(BaseTestVtexOrdersView):
    def setUp(self):
        self.user = User.objects.create()
        self.project = Project.objects.create(name="Test Project")

        self.client.force_authenticate(user=self.user)

    def test_get_utm_revenue_without_permission(self):
        response = self.get_utm_revenue()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_utm_revenue_without_project_uuid(self):
        response = self.get_utm_revenue()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_utm_revenue_without_required_fields(self):
        query_params = {
            "project_uuid": self.project.uuid,
        }

        response = self.get_utm_revenue(query_params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["feature"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    def test_cannot_get_utm_revenue_with_invalid_feature(self):
        query_params = {
            "project_uuid": self.project.uuid,
            "feature": "invalid_feature",
            "start_date": "2023-09-01",
            "end_date": "2023-09-04",
        }

        response = self.get_utm_revenue(query_params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["feature"][0].code, "invalid_feature")

    @with_project_auth
    def test_cannot_get_utm_revenue_with_invalid_date_format(self):
        query_params = {
            "project_uuid": self.project.uuid,
            "feature": "utm_revenue",
            "start_date": "2023-09-01",
            "end_date": "invalid_date_format",
        }

        response = self.get_utm_revenue(query_params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"][0].code, "invalid_date_format")

    @with_project_auth
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    @patch("insights.sources.orders.clients.VtexOrdersRestClient.list")
    def test_get_utm_revenue(self, mock_list, mock_get_vtex_auth):
        expected_utm_revenue = 50.21

        mock_list.return_value = {
            "countSell": 1,
            "accumulatedTotal": expected_utm_revenue,
            "ticketMax": 50.21,
            "ticketMin": 50.21,
            "medium_ticket": 50.21,
        }
        mock_get_vtex_auth.return_value = {
            "app_token": "fake_token",
            "app_key": "fake_key",
            "domain": "fake_domain",
        }

        query_params = {
            "project_uuid": self.project.uuid,
            "feature": "abandoned_cart",
            "start_date": "2023-09-01",
            "end_date": "2023-09-04",
        }

        response = self.get_utm_revenue(query_params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("utm_revenue", response.data)
        self.assertEqual(response.data["utm_revenue"], expected_utm_revenue)
