from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from insights.projects.models import Project
from insights.sources.vtex_conversions.usecases.query_execute import QueryExecutor
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


class TestQueryExecutor(TestCase):
    def setUp(self):
        self.project = Project.objects.create()
        self.query_executor = QueryExecutor()

    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    def test_get_vtex_credentials(self, mock_get_vtex_auth):
        mock_get_vtex_auth.return_value = {
            "app_key": "123",
            "app_token": "123",
            "domain": "example.myvtex.com",
        }
        credentials = self.query_executor.get_vtex_credentials(self.project)
        self.assertEqual(credentials, mock_get_vtex_auth.return_value)

    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    def test_get_vtex_credentials_raises_permission_denied(self, mock_get_vtex_auth):
        mock_get_vtex_auth.side_effect = VtexCredentialsNotFound()
        with self.assertRaises(PermissionDenied):
            self.query_executor.get_vtex_credentials(self.project)

    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    def test_get_vtex_credentials_raises_exception(self, mock_get_vtex_auth):
        mock_get_vtex_auth.side_effect = Exception("Error")
        with self.assertRaises(Exception):
            self.query_executor.get_vtex_credentials(self.project)
