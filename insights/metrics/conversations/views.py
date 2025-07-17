from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.serializers import (
    TopicsDistributionMetricsQueryParamsSerializer,
    TopicsDistributionMetricsSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(
        detail=False,
        methods=["get"],
        url_path="topics-distribution",
        url_name="topics-distribution",
        serializer_class=TopicsDistributionMetricsSerializer,
    )
    def topics_distribution(self, request: Request) -> Response:
        """
        Get subjects distribution
        """
        serializer = TopicsDistributionMetricsQueryParamsSerializer(
            data=request.query_params
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            metrics = self.service.get_topics_distribution(
                serializer.validated_data["project"],
                serializer.validated_data["start_date"],
                serializer.validated_data["end_date"],
            )
        except ConversationsMetricsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            TopicsDistributionMetricsSerializer(metrics).data,
            status=status.HTTP_200_OK,
        )
