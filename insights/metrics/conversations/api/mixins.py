from typing import Callable
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from sentry_sdk import capture_exception


from insights.metrics.conversations.exceptions import ConversationsMetricsError


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
