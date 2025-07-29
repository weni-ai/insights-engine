from uuid import UUID
import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.projects.models import Project
from insights.widgets.models import Widget


class BaseTestWidgetViewSet(APITestCase):
    def create_widget(self, data: dict) -> Response:
        url = reverse("widget-list")

        return self.client.post(url, data, format="json")

    def list_widgets(self) -> Response:
        url = reverse("widget-list")

        return self.client.get(url)

    def update_widget(self, widget_uuid: UUID, data: dict) -> Response:
        url = reverse("widget-detail", args=[widget_uuid])

        return self.client.patch(url, data, format="json")

    def delete_widget(self, widget_uuid: UUID) -> Response:
        url = reverse("widget-detail", args=[widget_uuid])

        return self.client.delete(url)


class TestWidgetViewSetAsAnonymousUser(BaseTestWidgetViewSet):
    def test_list_widgets(self) -> None:
        response = self.list_widgets()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_widget(self) -> None:
        response = self.create_widget({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_widget(self) -> None:
        response = self.update_widget(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_widget(self) -> None:
        response = self.delete_widget(uuid.uuid4())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestWidgetViewSetAsAuthenticationUser(BaseTestWidgetViewSet):
    def setUp(self):
        self.user = User.objects.create_user(email="test@email.com")
        self.project = Project.objects.create(
            name="testproject",
        )
        self.dashboard = Dashboard.objects.create(
            name="testdashboard",
            project=self.project,
        )

        self.client.force_authenticate(self.user)

    def _create_widget(self):
        return Widget.objects.create(
            name="testwidget",
            dashboard=self.dashboard,
            source="test",
            position=[],
            config={},
            type="test",
        )

    def test_list_widgets_without_permission(self):
        widget = self._create_widget()
        response = self.list_widgets()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(
            str(widget.uuid), {widget["uuid"] for widget in response.data["results"]}
        )

    @with_project_auth
    def test_list_widgets_with_permission(self):
        widget = self._create_widget()
        response = self.list_widgets()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(widget.uuid), {widget["uuid"] for widget in response.data["results"]}
        )

    def test_create_widget_without_permission(self):
        response = self.create_widget(
            {
                "name": "testwidget",
                "dashboard": self.dashboard.uuid,
                "source": "test",
                "position": [],
                "config": {},
                "type": "test",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_create_widget_with_permission(self):
        response = self.create_widget(
            {
                "name": "testwidget",
                "dashboard": self.dashboard.uuid,
                "source": "test",
                "position": [],
                "config": {},
                "type": "test",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_widget_without_permission(self):
        widget = self._create_widget()
        response = self.update_widget(widget.uuid, {"name": "testwidget2"})

        # The queryset excludes widgets that the user does not have permission to access
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @with_project_auth
    def test_update_and_configure_recurrence_widget(self):
        widget = self._create_widget()
        self.assertFalse(hasattr(widget, "report"))

        payload = {
            "type": "recurrence",
            "source": "flowruns",
            "config": {
                "operation": "recurrence",
                "op_field": "example",
                "limit": 5,
                "filter": {"flow": "cce1d832-c36f-49a7-9181-d65d3e7ff262"},
            },
        }

        response = self.update_widget(widget.uuid, payload)

        widget.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(hasattr(widget, "report"))

        expected_report_config = {
            "operation": widget.config.get("operation"),
            "op_field": widget.config.get("op_field"),
            "filter": widget.config.get("filter"),
            "data_suffix": "%",
        }

        self.assertEqual(widget.report.config, expected_report_config)
