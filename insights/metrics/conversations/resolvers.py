import logging
from typing import Optional
from uuid import UUID
from django.conf import settings
from rest_framework.request import Request
from sentry_sdk import capture_exception
from weni.feature_flags.shortcuts import is_feature_active_for_attributes

from insights.core.resolvers import BaseServiceResolver
from insights.metrics.conversations.services import (
    BaseConversationsMetricsService,
    ConversationsMetricsService,
)
from insights.metrics.conversations.mock.services import MockConversationsMetricsService


USE_MOCK_QUERY_PARAM_NAME = "use_mock"

logger = logging.getLogger(__name__)


class ConversationsMetricsServiceResolver(BaseServiceResolver):
    """
    Resolver for conversations metrics services
    """

    def _feature_flag_is_on(
        self, request: Optional[Request] = None, project_uuid: Optional[UUID] = None
    ) -> bool:
        """
        Check if the feature flag is on
        """
        try:
            attributes = {}

            if project_uuid is not None:
                attributes["projectUUID"] = str(project_uuid)

            if request is not None and request.user.is_authenticated:
                attributes["userEmail"] = request.user.email

            return is_feature_active_for_attributes(
                key=settings.CONVERSATIONS_DASHBOARD_MOCK_SERVICE_FEATURE_FLAG_KEY,
                attributes=attributes,
            )

        except Exception as e:
            logger.error(
                "[CONVERSATIONS METRICS SERVICE RESOLVER] Error checking if feature flag is on: %s. Defaulting to False.",
                e,
                exc_info=True,
            )
            capture_exception(e)

            return False

    def _should_use_mock_service(
        self,
        request: Optional[Request] = None,
        project_uuid: Optional[UUID] = None,
        force_use_real_service: bool = False,
    ) -> bool:
        """
        Check if the mock service should be used
        """
        query_params = request.query_params if request is not None else {}
        use_mock = query_params.get(USE_MOCK_QUERY_PARAM_NAME, False)

        if use_mock is True:
            return True

        if settings.CONVERSATIONS_DASHBOARD_FORCE_USE_MOCK_SERVICE:
            return True

        return (
            self._feature_flag_is_on(request, project_uuid)
            and not force_use_real_service
        )

    def resolve(
        self,
        request: Optional[Request] = None,
        project_uuid: Optional[UUID] = None,
        force_use_real_service: bool = False,
    ) -> BaseConversationsMetricsService:
        """
        Resolve a conversations metrics service

        Args:
            request: The request object
            force_use_real_service: Whether to force the use of the real service

        Returns:
            The conversations metrics service
        """

        if self._should_use_mock_service(request, project_uuid, force_use_real_service):
            return MockConversationsMetricsService

        return ConversationsMetricsService
