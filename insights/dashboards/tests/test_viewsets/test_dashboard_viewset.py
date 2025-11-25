import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response
from unittest.mock import patch

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth
from insights.widgets.models import Widget, Report


class BaseTestDashboardViewSet(APITestCase):
    def list(self, filters: dict = None) -> Response:
        url = reverse("dashboard-list")

        return self.client.get(url, filters)

    def update(self, dashboard_uuid: str, data: dict) -> Response:
        url = reverse("dashboard-detail", kwargs={"pk": dashboard_uuid})
        return self.client.patch(url, data, format="json")

    def destroy(self, dashboard_uuid: str) -> Response:
        url = reverse("dashboard-detail", kwargs={"pk": dashboard_uuid})
        return self.client.delete(url)

    def set_as_default(self, dashboard_uuid: str, data: dict) -> Response:
        url = reverse("dashboard-is-default", kwargs={"pk": dashboard_uuid})

        return self.client.patch(url, data, format="json")

    def list_widgets(self, dashboard_uuid: str) -> Response:
        url = reverse("dashboard-list-widgets", kwargs={"pk": dashboard_uuid})
        return self.client.get(url)

    def dashboard_filters(self, dashboard_uuid: str) -> Response:
        url = reverse("dashboard-filters", kwargs={"pk": dashboard_uuid})
        return self.client.get(url)

    def get_widget_data(self, dashboard_uuid: str, widget_uuid: str) -> Response:
        url = reverse(
            "dashboard-get-widget-data",
            kwargs={"pk": dashboard_uuid, "widget_uuid": widget_uuid},
        )
        return self.client.get(url)

    def get_widget_report(self, dashboard_uuid: str, widget_uuid: str) -> Response:
        url = reverse(
            "dashboard-get-widget-report",
            kwargs={"pk": dashboard_uuid, "widget_uuid": widget_uuid},
        )
        return self.client.get(url)

    def get_report_data(self, dashboard_uuid: str, widget_uuid: str) -> Response:
        url = reverse(
            "dashboard-get-report-data",
            kwargs={"pk": dashboard_uuid, "widget_uuid": widget_uuid},
        )
        return self.client.get(url)

    def list_sources(self, dashboard_uuid: str) -> Response:
        url = reverse("dashboard-list-sources", kwargs={"pk": dashboard_uuid})
        return self.client.get(url)

    def create_flows_dashboard(self, data: dict, project_uuid: str) -> Response:
        url = reverse("dashboard-create-flows-dashboard") + f"?project={project_uuid}"

        return self.client.post(url, data, format="json")

    def get_contacts_results(self, data: dict) -> Response:
        url = reverse("dashboard-get-contacts-results")
        return self.client.get(url, data)

    def get_custom_status(self, data: dict) -> Response:
        url = reverse("dashboard-get-custom-status")
        return self.client.get(url, data)

    def monitoring_csat_totals(self, dashboard_uuid: str, data: dict) -> Response:
        url = reverse("dashboard-monitoring-csat-totals", kwargs={"pk": dashboard_uuid})

        return self.client.get(url, data)

    def monitoring_csat_ratings(self, dashboard_uuid: str, data: dict) -> Response:
        url = reverse(
            "dashboard-monitoring-csat-ratings", kwargs={"pk": dashboard_uuid}
        )

        return self.client.get(url, data)

    def analysis_csat_ratings(self, dashboard_uuid: str, data: dict) -> Response:
        url = reverse("dashboard-analysis-csat-ratings", kwargs={"pk": dashboard_uuid})
        return self.client.get(url, data)


class TestDashboardViewSetAsAnonymousUser(BaseTestDashboardViewSet):
    def test_cannot_list_dashboards_when_unauthenticated(self):
        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_update_dashboard_when_unauthenticated(self):
        response = self.update("123", {"name": "Updated Dashboard Name"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_destroy_dashboard_when_unauthenticated(self):
        response = self.destroy("123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_set_dashboard_as_default_when_unauthenticated(self):
        response = self.set_as_default("123", {"is_default": True})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_list_widgets_when_unauthenticated(self):
        response = self.list_widgets("123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_dashboard_filters_when_unauthenticated(self):
        response = self.dashboard_filters("123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_widget_data_when_unauthenticated(self):
        response = self.get_widget_data("123", "123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_widget_report_when_unauthenticated(self):
        response = self.get_widget_report("123", "123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_report_data_when_unauthenticated(self):
        response = self.get_report_data("123", "123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_list_sources_when_unauthenticated(self):
        response = self.list_sources("123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_flows_dashboard_when_unauthenticated(self):
        response = self.create_flows_dashboard({"name": "Test Flows Dashboard"}, "123")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_contacts_results_when_unauthenticated(self):
        response = self.get_contacts_results(
            {"flow_uuid": "123", "project_uuid": "123"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_custom_status_when_unauthenticated(self):
        response = self.get_custom_status({"project": "123"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_monitoring_csat_totals_when_unauthenticated(self):
        response = self.monitoring_csat_totals(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_monitoring_csat_ratings_when_unauthenticated(self):
        response = self.monitoring_csat_ratings(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_analysis_csat_ratings_when_unauthenticated(self):
        response = self.analysis_csat_ratings(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDashboardViewSetAsAuthenticatedUser(BaseTestDashboardViewSet):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@test.com",
        )
        self.project = Project.objects.create(
            name="Test Project",
        )

        self.client.force_authenticate(user=self.user)

    @with_project_auth
    def test_list_dashboards(self):
        dashboard_1 = Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )

        # From another project, should not be listed
        dashboard_2 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=Project.objects.create(
                name="Test Project 2",
            ),
        )

        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_dashboards = {d["uuid"] for d in response.data["results"]}

        self.assertIn(str(dashboard_1.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_2.uuid), response_dashboards)

    def test_list_dashboards_without_project_auth(self):
        Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )
        response = self.list()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    @with_project_auth
    def test_list_dashboards_filtering_by_project(self):
        dashboard_1 = Dashboard.objects.create(
            name="Test Dashboard 1",
            project=self.project,
        )

        project_2 = Project.objects.create(
            name="Test Project 2",
        )
        ProjectAuth.objects.create(project=project_2, user=self.user, role=1)
        dashboard_2 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=project_2,
        )

        # From another project, should not be listed
        dashboard_3 = Dashboard.objects.create(
            name="Test Dashboard 2",
            project=Project.objects.create(
                name="Test Project 2",
            ),
        )

        response = self.list({"project": str(self.project.uuid)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_dashboards = {d["uuid"] for d in response.data["results"]}

        self.assertIn(str(dashboard_1.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_2.uuid), response_dashboards)
        self.assertNotIn(str(dashboard_3.uuid), response_dashboards)

    @with_project_auth
    def test_update_dashboard(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_editable=True,
        )
        response = self.update(str(dashboard.uuid), {"name": "Updated Dashboard Name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.name, "Updated Dashboard Name")

    @with_project_auth
    def test_update_dashboard_not_editable(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_editable=False,
        )
        response = self.update(str(dashboard.uuid), {"name": "Updated Dashboard Name"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_destroy_dashboard(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_deletable=True,
        )
        response = self.destroy(str(dashboard.uuid))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dashboard.objects.filter(uuid=dashboard.uuid).exists())

    @with_project_auth
    def test_destroy_dashboard_not_deletable(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_deletable=False,
        )
        response = self.destroy(str(dashboard.uuid))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_set_dashboard_as_default(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_default=False,
        )
        response = self.set_as_default(str(dashboard.uuid), {"is_default": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.is_default)

    @with_project_auth
    def test_unset_dashboard_as_default(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_default=True,
        )
        response = self.set_as_default(str(dashboard.uuid), {"is_default": False})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.is_default)

    @with_project_auth
    def test_list_widgets(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget1 = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )
        widget2 = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 2",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )

        response = self.list_widgets(str(dashboard.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_widgets = {w["uuid"] for w in response.data["results"]}
        self.assertIn(str(widget1.uuid), response_widgets)
        self.assertIn(str(widget2.uuid), response_widgets)

    @with_project_auth
    def test_dashboard_filters(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        response = self.dashboard_filters(str(dashboard.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    @with_project_auth
    @patch("insights.dashboards.viewsets.get_source_data_from_widget")
    def test_get_widget_data(self, mock_get_source_data):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )
        mock_get_source_data.return_value = {"data": "mocked_widget_data"}

        response = self.get_widget_data(str(dashboard.uuid), str(widget.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"data": "mocked_widget_data"})
        mock_get_source_data.assert_called_once_with(
            widget=widget,
            is_report=False,
            is_live=False,
            filters={},
            user_email=self.user.email,
        )

    @with_project_auth
    def test_get_widget_report(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )
        report = Report.objects.create(
            widget=widget,
            name="Report 1",
            source="TestSource",
            type="TestType",
            config={},
        )

        response = self.get_widget_report(str(dashboard.uuid), str(widget.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(report.uuid))

    @with_project_auth
    def test_get_widget_report_widget_not_found(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        non_existent_widget_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        response = self.get_widget_report(str(dashboard.uuid), non_existent_widget_uuid)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @with_project_auth
    def test_get_widget_report_report_not_found(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )

        response = self.get_widget_report(str(dashboard.uuid), str(widget.uuid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @with_project_auth
    @patch("insights.dashboards.viewsets.get_source_data_from_widget")
    def test_get_report_data(self, mock_get_source_data):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="TestSource",
            type="TestType",
            config={},
            position={},
        )
        Report.objects.create(
            widget=widget,
            name="Report 1",
            source="TestSource",
            type="TestType",
            config={},
        )
        mock_get_source_data.return_value = {"data": "mocked_report_data"}

        response = self.get_report_data(str(dashboard.uuid), str(widget.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"data": "mocked_report_data"})
        mock_get_source_data.assert_called_once_with(
            widget=widget,
            is_report=True,
            filters={},
            user_email=self.user.email,
            is_live=False,
        )

    @with_project_auth
    def test_list_sources(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        widget1 = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 1",
            source="Source1",
            type="TestType",
            config={},
            position={},
        )
        widget2 = Widget.objects.create(
            dashboard=dashboard,
            name="Widget 2",
            source="Source2",
            type="TestType",
            config={},
            position={},
        )

        response = self.list_sources(str(dashboard.uuid))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_sources = [s["source"] for s in response.data["results"]]
        self.assertIn(widget1.source, response_sources)
        self.assertIn(widget2.source, response_sources)

    @with_project_auth
    @patch("insights.dashboards.viewsets.CreateFlowsDashboard")
    def test_create_flows_dashboard(self, MockCreateFlowsDashboard):
        mock_dashboard_instance = Dashboard(
            name="Flows Dashboard", project=self.project
        )
        mock_create_dashboard = MockCreateFlowsDashboard.return_value
        mock_create_dashboard.create_dashboard.return_value = mock_dashboard_instance

        data = {
            "name": "New Flows Dashboard",
            "funnel_amount": 1000,
            "currency_type": "USD",
        }
        response = self.create_flows_dashboard(data, str(self.project.uuid))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["dashboard"]["name"], "Flows Dashboard")
        MockCreateFlowsDashboard.assert_called_once()

    @with_project_auth
    @patch("insights.dashboards.viewsets.CreateFlowsDashboard")
    def test_create_flows_dashboard_project_not_found(self, MockCreateFlowsDashboard):
        data = {
            "name": "New Flows Dashboard",
        }
        response = self.create_flows_dashboard(data, str(uuid.uuid4()))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        MockCreateFlowsDashboard.assert_not_called()

    @with_project_auth
    @patch("insights.dashboards.viewsets.FlowsContactsRestClient")
    def test_get_contacts_results(self, MockFlowsContactsRestClient):
        mock_client_instance = MockFlowsContactsRestClient.return_value
        mock_client_instance.get_flows_contacts.return_value = {"contacts": []}

        params = {
            "flow_uuid": "some-flow-uuid",
            "project_uuid": str(self.project.uuid),
            "user_email": self.user.email,
        }
        response = self.get_contacts_results(params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"contacts": []})
        mock_client_instance.get_flows_contacts.assert_called_once_with(
            flow_uuid="some-flow-uuid",
            page_number=None,
            page_size=None,
            project_uuid=str(self.project.uuid),
            op_field=None,
            label=None,
            user=self.user.email,
            ended_at_gte=None,
            ended_at_lte=None,
        )

    @with_project_auth
    @patch("insights.dashboards.viewsets.CustomStatusRESTClient")
    def test_get_custom_status(self, MockCustomStatusRESTClient):
        mock_client_instance = MockCustomStatusRESTClient.return_value
        mock_client_instance.list_custom_status.return_value = {"status": "ok"}

        response = self.get_custom_status({"project": str(self.project.uuid)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
        MockCustomStatusRESTClient.assert_called_once_with(self.project)
        mock_client_instance.list_custom_status.assert_called_once_with(
            {"project": [str(self.project.uuid)]}
        )

    @with_project_auth
    @patch("insights.dashboards.viewsets.CustomStatusRESTClient")
    def test_get_custom_status_project_not_found(self, MockCustomStatusRESTClient):
        non_existent_project_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        response = self.get_custom_status({"project": non_existent_project_uuid})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        MockCustomStatusRESTClient.assert_not_called()

    @with_project_auth
    @patch("insights.dashboards.viewsets.HumanSupportDashboardService")
    def test_get_monitoring_csat_totals(self, MockHumanSupportDashboardService):
        mock_service_instance = MockHumanSupportDashboardService.return_value
        mock_service_instance.csat_score_by_agents.return_value = {
            "general": {"rooms": 0, "reviews": 0, "avg_rating": None},
            "next": None,
            "previous": None,
            "results": [
                {
                    "agent": {"name": "Test Agent", "email": "kallil@test.com"},
                    "rooms": 0,
                    "reviews": 0,
                    "avg_rating": 0.0,
                },
            ],
        }

        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        response = self.monitoring_csat_totals(str(dashboard.uuid), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    @patch("insights.dashboards.viewsets.HumanSupportDashboardService")
    def test_get_monitoring_csat_ratings(self, MockHumanSupportDashboardService):
        mock_service_instance = MockHumanSupportDashboardService.return_value
        mock_service_instance.get_csat_ratings.return_value = {
            "1": {
                "value": 20.0,
                "full_value": 20,
            },
            "2": {
                "value": 20.0,
                "full_value": 20,
            },
            "3": {
                "value": 20.0,
                "full_value": 20,
            },
            "4": {
                "value": 20.0,
                "full_value": 20,
            },
            "5": {
                "value": 20.0,
                "full_value": 20,
            },
        }

        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        response = self.monitoring_csat_ratings(str(dashboard.uuid), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "1": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "2": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "3": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "4": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "5": {
                    "value": 20.0,
                    "full_value": 20,
                },
            },
        )

    @with_project_auth
    @patch("insights.dashboards.viewsets.HumanSupportDashboardService")
    def test_get_analysis_csat_ratings(self, MockHumanSupportDashboardService):
        mock_service_instance = MockHumanSupportDashboardService.return_value
        mock_service_instance.get_csat_ratings.return_value = {
            "1": {
                "value": 20.0,
                "full_value": 20,
            },
            "2": {
                "value": 20.0,
                "full_value": 20,
            },
            "3": {
                "value": 20.0,
                "full_value": 20,
            },
            "4": {
                "value": 20.0,
                "full_value": 20,
            },
            "5": {
                "value": 20.0,
                "full_value": 20,
            },
        }

        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        response = self.analysis_csat_ratings(str(dashboard.uuid), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "1": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "2": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "3": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "4": {
                    "value": 20.0,
                    "full_value": 20,
                },
                "5": {
                    "value": 20.0,
                    "full_value": 20,
                },
            },
        )
