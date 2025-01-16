from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from insights.dashboards.models import Dashboard
from insights.projects.models import Project, ProjectAuth, Roles
from insights.users.models.user import User
from insights.widgets.models import Widget


class TestUpdateWidget(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@email.com")
        project = Project.objects.create()

        ProjectAuth.objects.create(user=self.user, project=project, role=Roles.ADMIN)

        dashboard = Dashboard.objects.create(
            project=project,
            name="test",
            description="test",
        )
        self.widget = Widget.objects.create(
            dashboard=dashboard,
            source="",
            position={"rows": [1, 3], "columns": [9, 12]},
            config={},
            type="recurrence",
        )

        self.token = Token.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user, token=self.token)

    def test_update_and_configure_recurrence_widget(self):
        self.assertFalse(hasattr(self.widget, "report"))

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

        url = f"/v1/widgets/{self.widget.uuid}/"
        response = self.client.patch(
            url,
            payload,
            format="json",
        )

        self.widget.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(hasattr(self.widget, "report"))

        expected_report_config = {
            "operation": self.widget.config.get("operation"),
            "op_field": self.widget.config.get("op_field"),
            "filter": self.widget.config.get("filter"),
            "data_suffix": "%",
        }

        self.assertEqual(self.widget.report.config, expected_report_config)
