from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase, override_settings

from insights.metrics.conversations.mock.services import MockConversationsMetricsService
from insights.metrics.conversations.resolvers import ConversationsMetricsServiceResolver
from insights.metrics.conversations.services import ConversationsMetricsService


RESOLVER_MODULE = "insights.metrics.conversations.resolvers"


class ConversationsMetricsServiceResolverTests(TestCase):
    """
    Tests for the ConversationsMetricsServiceResolver class
    """

    def setUp(self):
        self.resolver = ConversationsMetricsServiceResolver()

    def _make_request(self, query_params=None, user=None):
        request = MagicMock()
        request.query_params = query_params or {}
        if user is None:
            request.user.is_authenticated = False
        else:
            request.user = user
            request.user.is_authenticated = True
        return request

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_when_feature_flag_is_on(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = True

        result = self.resolver.resolve()
        self.assertEqual(result, MockConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_when_feature_flag_is_off(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        result = self.resolver.resolve()
        self.assertEqual(result, ConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_when_feature_flag_is_on_but_force_use_real_service(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = True

        result = self.resolver.resolve(force_use_real_service=True)
        self.assertEqual(result, ConversationsMetricsService)

    @override_settings(CONVERSATIONS_DASHBOARD_FORCE_USE_MOCK_SERVICE=True)
    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_when_force_mock_setting_is_true(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        result = self.resolver.resolve()
        self.assertEqual(result, MockConversationsMetricsService)

    @override_settings(CONVERSATIONS_DASHBOARD_FORCE_USE_MOCK_SERVICE=True)
    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_force_mock_setting_ignores_force_use_real_service(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False

        result = self.resolver.resolve(force_use_real_service=True)
        self.assertEqual(result, MockConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_with_use_mock_query_param(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        request = self._make_request(query_params={"use_mock": True})

        result = self.resolver.resolve(request=request)
        self.assertEqual(result, MockConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_with_request_and_flag_off(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = False
        request = self._make_request()

        result = self.resolver.resolve(request=request)
        self.assertEqual(result, ConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_with_authenticated_request_and_flag_on(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = True
        user = MagicMock()
        user.is_authenticated = True
        user.email = "test@example.com"
        request = self._make_request(user=user)

        result = self.resolver.resolve(request=request)
        self.assertEqual(result, MockConversationsMetricsService)
        call_kwargs = mock_is_feature_active_for_attributes.call_args
        self.assertIn("userEmail", call_kwargs.kwargs.get("attributes", {}))

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_without_request(self, mock_is_feature_active_for_attributes):
        mock_is_feature_active_for_attributes.return_value = False

        result = self.resolver.resolve(request=None)
        self.assertEqual(result, ConversationsMetricsService)

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_with_project_uuid_passes_attribute(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.return_value = True
        project_uuid = uuid4()

        result = self.resolver.resolve(project_uuid=project_uuid)
        self.assertEqual(result, MockConversationsMetricsService)
        call_kwargs = mock_is_feature_active_for_attributes.call_args
        self.assertEqual(
            call_kwargs.kwargs.get("attributes", {}).get("projectUUID"),
            str(project_uuid),
        )

    @patch(f"{RESOLVER_MODULE}.is_feature_active_for_attributes")
    def test_resolve_defaults_to_real_service_when_feature_flag_raises(
        self, mock_is_feature_active_for_attributes
    ):
        mock_is_feature_active_for_attributes.side_effect = Exception("boom")

        result = self.resolver.resolve()
        self.assertEqual(result, ConversationsMetricsService)
