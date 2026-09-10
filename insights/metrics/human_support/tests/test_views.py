from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.projects.models import Project

SERVICE_PATH = "insights.human_support.services.HumanSupportDashboardService"


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


TOTAL_REVENUE_RESPONSE = {
    "value": 428450.0,
    "previous_value": 362480.0,
    "currency_code": "USD",
    "increase_percentage": 18.2,
}


class TestTotalRevenueViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/sales/total-revenue/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTotalRevenueView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/sales/total-revenue/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_total_revenue")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = TOTAL_REVENUE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, TOTAL_REVENUE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_total_revenue")
    def test_forwards_period_and_comparison_filters(self, mock_service_method):
        mock_service_method.return_value = TOTAL_REVENUE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "comparison_start_date": "2025-03-01",
                "comparison_end_date": "2025-03-31",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2025-04-01")
        self.assertEqual(filters["end_date"], "2025-04-30")
        self.assertEqual(filters["comparison_start_date"], "2025-03-01")
        self.assertEqual(filters["comparison_end_date"], "2025-03-31")


class TestTotalRevenueViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/sales/total-revenue/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTotalRevenueViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/sales/total-revenue/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_total_revenue")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = TOTAL_REVENUE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, TOTAL_REVENUE_RESPONSE)
        mock_service_method.assert_called_once()


AVERAGE_ORDER_VALUE_RESPONSE = {
    "value": 150.0,
    "previous_value": 100.0,
    "currency_code": "USD",
    "increase_percentage": 50.0,
}


class TestAverageOrderValueViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/sales/average-order-value/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAverageOrderValueView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/sales/average-order-value/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_average_order_value")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = AVERAGE_ORDER_VALUE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, AVERAGE_ORDER_VALUE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_average_order_value")
    def test_forwards_period_and_comparison_filters(self, mock_service_method):
        mock_service_method.return_value = AVERAGE_ORDER_VALUE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "comparison_start_date": "2025-03-01",
                "comparison_end_date": "2025-03-31",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2025-04-01")
        self.assertEqual(filters["end_date"], "2025-04-30")
        self.assertEqual(filters["comparison_start_date"], "2025-03-01")
        self.assertEqual(filters["comparison_end_date"], "2025-03-31")


class TestAverageOrderValueViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/sales/average-order-value/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAverageOrderValueViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/sales/average-order-value/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_average_order_value")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = AVERAGE_ORDER_VALUE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, AVERAGE_ORDER_VALUE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_average_order_value")
    def test_forwards_period_and_comparison_filters(self, mock_service_method):
        mock_service_method.return_value = AVERAGE_ORDER_VALUE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "comparison_start_date": "2025-03-01",
                "comparison_end_date": "2025-03-31",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2025-04-01")
        self.assertEqual(filters["end_date"], "2025-04-30")
        self.assertEqual(filters["comparison_start_date"], "2025-03-01")
        self.assertEqual(filters["comparison_end_date"], "2025-03-31")


SALES_FUNNEL_RESPONSE = {
    "leads_captured": {"full_value": 45000, "value": 100.0},
    "purchases_made": {"full_value": 4250, "value": 9.44},
}


class TestSalesFunnelViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/sales/sales-funnel/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSalesFunnelView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/sales/sales-funnel/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_sales_funnel")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = SALES_FUNNEL_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, SALES_FUNNEL_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_sales_funnel")
    def test_forwards_period_filters(self, mock_service_method):
        mock_service_method.return_value = SALES_FUNNEL_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")


class TestSalesFunnelViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/sales/sales-funnel/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSalesFunnelViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/sales/sales-funnel/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_sales_funnel")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = SALES_FUNNEL_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, SALES_FUNNEL_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_sales_funnel")
    def test_forwards_period_filters(self, mock_service_method):
        mock_service_method.return_value = SALES_FUNNEL_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")


CHANNEL_REVENUE_SALE_RESPONSE = {
    "metric": "sale",
    "currency_code": "",
    "count": 6,
    "results": [
        {"channel": "whatsapp", "value": 620, "percentage": 21.75},
        {"channel": "teams", "value": 510, "percentage": 17.89},
        {"channel": "email", "value": 460, "percentage": 16.14},
        {"channel": "instagram", "value": 390, "percentage": 13.68},
        {"channel": "facebook", "value": 330, "percentage": 11.58},
        {"channel": "others", "value": 330, "percentage": 11.58},
    ],
}


class TestChannelRevenueSaleViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/sales/channel-revenue/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestChannelRevenueSaleView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/sales/channel-revenue/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_channel_revenue_sale")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = CHANNEL_REVENUE_SALE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, CHANNEL_REVENUE_SALE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_channel_revenue_sale")
    def test_forwards_period_and_metric_filters(self, mock_service_method):
        mock_service_method.return_value = CHANNEL_REVENUE_SALE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "metric": "revenue",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")
        self.assertEqual(filters["metric"], "revenue")


class TestChannelRevenueSaleViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/sales/channel-revenue/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestChannelRevenueSaleViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/sales/channel-revenue/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_channel_revenue_sale")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = CHANNEL_REVENUE_SALE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, CHANNEL_REVENUE_SALE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_channel_revenue_sale")
    def test_forwards_period_and_metric_filters(self, mock_service_method):
        mock_service_method.return_value = CHANNEL_REVENUE_SALE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "metric": "sale",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")
        self.assertEqual(filters["metric"], "sale")


PERFORMANCE_BY_REPRESENTATIVE_RESPONSE = {
    "currency_code": "USD",
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "representative": "Emma Wilson",
            "conversations": 612,
            "sales": 254,
            "conversion": 41.5,
            "revenue": 72340.0,
            "average_order_value": 285.0,
            "trend": 12.4,
        }
    ],
}


class TestPerformanceByRepresentativeViewAsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v1/metrics/human-support/sales/performance-by-representative/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPerformanceByRepresentativeView(BaseHumanSupportViewTest):
    URL = "/v1/metrics/human-support/sales/performance-by-representative/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_performance_by_representative")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = PERFORMANCE_BY_REPRESENTATIVE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PERFORMANCE_BY_REPRESENTATIVE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_performance_by_representative")
    def test_forwards_filters_that_affect_the_table(self, mock_service_method):
        mock_service_method.return_value = PERFORMANCE_BY_REPRESENTATIVE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "comparison_start_date": "2026-07-25",
                "comparison_end_date": "2026-07-31",
                "agent": "emma@example.com",
                "ordering": "-revenue",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")
        self.assertEqual(filters["comparison_start_date"], "2026-07-25")
        self.assertEqual(filters["comparison_end_date"], "2026-07-31")
        self.assertEqual(filters["agent"], "emma@example.com")
        self.assertEqual(filters["ordering"], "-revenue")


class TestPerformanceByRepresentativeViewV2AsAnonymous(APITestCase):
    def test_returns_401_when_unauthenticated(self):
        url = "/v2/metrics/human-support/sales/performance-by-representative/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPerformanceByRepresentativeViewV2(BaseHumanSupportViewTest):
    URL = "/v2/metrics/human-support/sales/performance-by-representative/"

    def test_returns_400_without_project_uuid(self):
        response = self.client.get(self.URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_403_without_project_auth(self):
        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_performance_by_representative")
    def test_returns_200_with_valid_request(self, mock_service_method):
        mock_service_method.return_value = PERFORMANCE_BY_REPRESENTATIVE_RESPONSE

        response = self.client.get(self.URL, {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PERFORMANCE_BY_REPRESENTATIVE_RESPONSE)
        mock_service_method.assert_called_once()

    @with_project_auth
    @patch(f"{SERVICE_PATH}.get_performance_by_representative")
    def test_forwards_filters_that_affect_the_table(self, mock_service_method):
        mock_service_method.return_value = PERFORMANCE_BY_REPRESENTATIVE_RESPONSE

        self.client.get(
            self.URL,
            {
                "project_uuid": self.project.uuid,
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "comparison_start_date": "2026-07-25",
                "comparison_end_date": "2026-07-31",
                "agent": "emma@example.com",
                "ordering": "-revenue",
            },
        )

        filters = mock_service_method.call_args[1]["filters"]
        self.assertEqual(filters["start_date"], "2026-08-01")
        self.assertEqual(filters["end_date"], "2026-08-07")
        self.assertEqual(filters["comparison_start_date"], "2026-07-25")
        self.assertEqual(filters["comparison_end_date"], "2026-07-31")
        self.assertEqual(filters["agent"], "emma@example.com")
        self.assertEqual(filters["ordering"], "-revenue")
