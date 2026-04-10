from typing import Callable
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from insights.metrics.conversations.resolvers import ConversationsMetricsServiceResolver
from insights.metrics.conversations.services import BaseConversationsMetricsService


class ConversationsMetricsResponseMixin:
    """
    Mixin to handle responses from the conversations metrics service.
    """

    def prepare_metrics_response(
        self,
        method: Callable,
        serializer: serializers.Serializer,
        metrics_kwargs: dict,
    ) -> Response:
        """
        Prepare the response for the metrics endpoint.
        """
        metrics = method(**metrics_kwargs)
        return Response(serializer(metrics).data, status=status.HTTP_200_OK)


class ConversationsMetricsServiceResolverMixin:
    """
    Mixin to get the correct service for the conversations metrics endpoints
    """

    _resolver = None
    _service = None

    @property
    def resolver(self) -> ConversationsMetricsServiceResolver:
        if self._resolver is None:
            self._resolver = ConversationsMetricsServiceResolver()

        return self._resolver

    @property
    def service(self) -> BaseConversationsMetricsService:
        if self._service is None:
            query_params = self.request.query_params
            project_uuid = query_params.get("project_uuid")

            try:
                action = getattr(self, self.action)
                force_use_real_service = getattr(
                    action, "force_use_real_service", False
                )
            except AttributeError:
                force_use_real_service = False

            self._service = self.resolver.resolve(
                request=self.request,
                project_uuid=project_uuid,
                force_use_real_service=force_use_real_service,
            )()

        return self._service


class ConversationsMetricsResponseMixin:
    """
    Mixin to handle responses from the conversations metrics service.
    """

    def prepare_metrics_response(
        self,
        method: Callable,
        serializer: serializers.Serializer,
        metrics_kwargs: dict,
    ) -> Response:
        """
        Prepare the response for the metrics endpoint.
        """
        try:
            metrics = method(**metrics_kwargs)
        except (ConversationsMetricsError, Exception) as e:
            # When a generic internal error occurs, we capture the exception and return a 500 error
            # with Sentry's event ID for debugging purposes.
            event_id = capture_exception(e)
            return Response(
                {
                    "error": f"Failed to get {method.__name__} metrics. Event ID: {event_id}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serializer(metrics).data, status=status.HTTP_200_OK)
