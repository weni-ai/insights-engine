from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.projects.models import Project


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

        self.client.force_authenticate(self.user)
