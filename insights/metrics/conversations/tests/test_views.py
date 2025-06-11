from rest_framework.test import APITestCase


class BaseTestConversationsMetricsViewSet(APITestCase):
    pass


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    pass


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    pass
