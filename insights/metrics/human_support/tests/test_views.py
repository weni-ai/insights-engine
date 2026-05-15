from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project


SERVICE_PATH = (
    "insights.human_support.services.HumanSupportDashboardService"
)


class BaseHumanSupportViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.client.force_authenticate(self.user)


class TestDetailedMonitoringOnGoingViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/detailed-monitoring/on-going/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringOnGoingView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/detailed-monitoring/on-going/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_on_going")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"results": [], "count": 0}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"results": [], "count": 0})
        mock_service_method.assert_called_once()


class TestDetailedMonitoringAwaitingViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/detailed-monitoring/awaiting/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringAwaitingView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/detailed-monitoring/awaiting/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_awaiting")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"results": [], "count": 0}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"results": [], "count": 0})
        mock_service_method.assert_called_once()


class TestDetailedMonitoringAgentsViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/detailed-monitoring/agents/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringAgentsView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/detailed-monitoring/agents/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_agents")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {
            "results": [
                {"agent": "Agent 1", "status": "online"},
                {"agent": "Agent 2", "status": "offline"},
            ]
        }

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        mock_service_method.assert_called_once()


class TestDetailedMonitoringStatusViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/detailed-monitoring/status/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringStatusView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/detailed-monitoring/status/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_status")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"online": 5, "offline": 3}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"online": 5, "offline": 3})
        mock_service_method.assert_called_once()


class TestDetailedMonitoringAgentsTotalsViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/detailed-monitoring/agents_totals/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringAgentsTotalsView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/detailed-monitoring/agents_totals/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_agents_totals")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"total": 10, "online": 7}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"total": 10, "online": 7})
        mock_service_method.assert_called_once()


class TestAnalysisDetailedMonitoringStatusViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/analysis/detailed-monitoring/status/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAnalysisDetailedMonitoringStatusView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/analysis/detailed-monitoring/status/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_analysis_detailed_monitoring_status")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"status": "active", "count": 5}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "active", "count": 5})
        mock_service_method.assert_called_once()


# --- V2 Views ---


class TestDetailedMonitoringAgentsViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/detailed-monitoring/agents/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringAgentsViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/detailed-monitoring/agents/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_agents_v2")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {
            "count": 2,
            "results": [
                {"agent": "Agent 1", "status": "online"},
                {"agent": "Agent 2", "status": "offline"},
            ],
        }

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        mock_service_method.assert_called_once()


class TestDetailedMonitoringStatusViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/detailed-monitoring/status/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDetailedMonitoringStatusViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/detailed-monitoring/status/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_detailed_monitoring_status_v2")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"online": 5, "offline": 3}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"online": 5, "offline": 3})
        mock_service_method.assert_called_once()


class TestAnalysisDetailedMonitoringStatusViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/analysis/detailed-monitoring/status/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAnalysisDetailedMonitoringStatusViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/analysis/detailed-monitoring/status/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_analysis_detailed_monitoring_status_v2")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = {"status": "active", "count": 5}

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "active", "count": 5})
        mock_service_method.assert_called_once()
