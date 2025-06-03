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


class TestDashboardViewSetAsAnonymousUser(BaseTestDashboardViewSet):
    def test_cannot_list_dashboards_when_unauthenticated(self):
        response = self.list()

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
        url = reverse("dashboard-detail", kwargs={"pk": str(dashboard.uuid)})
        data = {"name": "Updated Dashboard Name"}
        response = self.client.patch(url, data)
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
        url = reverse("dashboard-detail", kwargs={"pk": str(dashboard.uuid)})
        data = {"name": "Updated Dashboard Name"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_destroy_dashboard(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_deletable=True,
        )
        url = reverse("dashboard-detail", kwargs={"pk": str(dashboard.uuid)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dashboard.objects.filter(uuid=dashboard.uuid).exists())

    @with_project_auth
    def test_destroy_dashboard_not_deletable(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_deletable=False,
        )
        url = reverse("dashboard-detail", kwargs={"pk": str(dashboard.uuid)})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_set_dashboard_as_default(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
            is_default=False,
        )
        url = reverse("dashboard-is-default", kwargs={"pk": str(dashboard.uuid)})
        data = {"is_default": True}
        response = self.client.patch(url, data)
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
        url = reverse("dashboard-is-default", kwargs={"pk": str(dashboard.uuid)})
        data = {"is_default": False}
        response = self.client.patch(url, data)
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

        url = reverse("dashboard-list-widgets", kwargs={"pk": str(dashboard.uuid)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_widgets = {w["uuid"] for w in response.data["results"]}
        self.assertIn(str(widget1.uuid), response_widgets)
        self.assertIn(str(widget2.uuid), response_widgets)

    @with_project_auth
    def test_dashboard_filters(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        url = reverse("dashboard-filters", kwargs={"pk": str(dashboard.uuid)})
        response = self.client.get(url)

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

        url = reverse(
            "dashboard-get-widget-data",
            kwargs={"pk": str(dashboard.uuid), "widget_uuid": str(widget.uuid)},
        )
        response = self.client.get(url)

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

        url = reverse(
            "dashboard-get-widget-report",
            kwargs={"pk": str(dashboard.uuid), "widget_uuid": str(widget.uuid)},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(report.uuid))

    @with_project_auth
    def test_get_widget_report_widget_not_found(self):
        dashboard = Dashboard.objects.create(
            name="Test Dashboard", project=self.project
        )
        non_existent_widget_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        url = reverse(
            "dashboard-get-widget-report",
            kwargs={"pk": str(dashboard.uuid), "widget_uuid": non_existent_widget_uuid},
        )
        response = self.client.get(url)
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

        url = reverse(
            "dashboard-get-widget-report",
            kwargs={"pk": str(dashboard.uuid), "widget_uuid": str(widget.uuid)},
        )
        response = self.client.get(url)
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

        url = reverse(
            "dashboard-get-report-data",
            kwargs={"pk": str(dashboard.uuid), "widget_uuid": str(widget.uuid)},
        )
        response = self.client.get(url)

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

        url = reverse("dashboard-list-sources", kwargs={"pk": str(dashboard.uuid)})
        response = self.client.get(url)

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

        url = (
            reverse("dashboard-create-flows-dashboard")
            + f"?project={self.project.uuid}"
        )
        data = {
            "name": "New Flows Dashboard",
            "funnel_amount": 1000,
            "currency_type": "USD",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["dashboard"]["name"], "Flows Dashboard")
        MockCreateFlowsDashboard.assert_called_once()

    @with_project_auth
    @patch("insights.dashboards.viewsets.CreateFlowsDashboard")
    def test_create_flows_dashboard_project_not_found(self, MockCreateFlowsDashboard):
        non_existent_project_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        url = (
            reverse("dashboard-create-flows-dashboard")
            + f"?project={non_existent_project_uuid}"
        )
        data = {
            "name": "New Flows Dashboard",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        MockCreateFlowsDashboard.assert_not_called()

    @with_project_auth
    @patch("insights.dashboards.viewsets.FlowsContactsRestClient")
    def test_get_contacts_results(self, MockFlowsContactsRestClient):
        mock_client_instance = MockFlowsContactsRestClient.return_value
        mock_client_instance.get_flows_contacts.return_value = {"contacts": []}

        url = reverse("dashboard-get-contacts-results")
        params = {
            "flow_uuid": "some-flow-uuid",
            "project_uuid": str(self.project.uuid),
            "user_email": self.user.email,
        }
        response = self.client.get(url, params)

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
        mock_client_instance.list.return_value = {"status": "ok"}

        url = reverse("dashboard-get-custom-status") + f"?project={self.project.uuid}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
        MockCustomStatusRESTClient.assert_called_once_with(self.project)
        mock_client_instance.list.assert_called_once_with(
            {"project": [str(self.project.uuid)]}
        )

    @with_project_auth
    @patch("insights.dashboards.viewsets.CustomStatusRESTClient")
    def test_get_custom_status_project_not_found(self, MockCustomStatusRESTClient):
        non_existent_project_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        url = (
            reverse("dashboard-get-custom-status")
            + f"?project={non_existent_project_uuid}"
        )
        with self.assertRaises(Project.DoesNotExist):
            self.client.get(url)

        MockCustomStatusRESTClient.assert_not_called()
