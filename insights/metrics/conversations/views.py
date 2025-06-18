from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    SubjectsDistributionMetricsQueryParamsSerializer,
    SubjectsDistributionMetricsSerializer,
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
        url_path="subjects-distribution",
        url_name="subjects-distribution",
        serializer_class=SubjectsDistributionMetricsSerializer,
    )
    def subjects_distribution(self, request: Request) -> Response:
        """
        Get subjects distribution
        """
        serializer = SubjectsDistributionMetricsQueryParamsSerializer(
            data=request.query_params
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        metrics = self.service.get_subjects_distribution(
            serializer.validated_data["project"],
            serializer.validated_data["start_date"],
            serializer.validated_data["end_date"],
        )
        return Response(
            SubjectsDistributionMetricsSerializer(metrics).data,
            status=status.HTTP_200_OK,
        )
