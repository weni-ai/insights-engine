from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action

from insights.metrics.conversations.services import ConversationsMetricsService
from insights.sources.integrations.clients import NexusClient


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()

    @action(detail=False, methods=["get"])
    def topics(self, request: Request, *args, **kwargs):
        """
        Get conversation topics
        """

        nexus_client = NexusClient()
        response_content, status_code = nexus_client.get_topics(
            request.user.project_uuid
        )

        return Response(response_content, status=status_code)
