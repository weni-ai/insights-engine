from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

from insights.metrics.conversations.serializers import SubjectsMetricsSerializer
from insights.metrics.conversations.services import ConversationsMetricsService


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()

    @action(detail=False, methods=["get"], serializer_class=SubjectsMetricsSerializer)
    def subjects(self, request: Request) -> Response:
        pass
