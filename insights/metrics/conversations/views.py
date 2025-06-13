from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    RoomsByQueueMetricQueryParamsSerializer,
    RoomsByQueueMetricSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(detail=False, methods=["get"])
    def queues(self, request: Request) -> Response:
        query_params = RoomsByQueueMetricQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)

        rooms_by_queue = self.service.get_rooms_numbers_by_queue(
            project_uuid=query_params.validated_data["project_uuid"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            limit=query_params.validated_data.get("limit", None),
        )

        serializer = RoomsByQueueMetricSerializer(rooms_by_queue)
        return Response(serializer.data, status=status.HTTP_200_OK)
