from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.dashboards.models import Dashboard
from insights.projects.models import Project
from insights.widgets.models import Widget


class BaseTestConversationsMetricsViewSet(APITestCase):
    pass


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    pass


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        self.client.force_authenticate(self.user)

    def test_get_csat_metrics(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
        )
