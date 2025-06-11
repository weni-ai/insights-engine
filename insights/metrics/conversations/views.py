from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
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
        serializer_class=ConversationTotalsMetricsSerializer,
    )
    def totals(self, request: Request, *args, **kwargs) -> Response:
        """
        Get conversations metrics totals
        """

        query_params_serializer = ConversationTotalsMetricsQueryParamsSerializer(
            data=request.query_params,
        )
        query_params_serializer.is_valid(raise_exception=True)

        totals = self.service.get_totals(
            project=self.get_object(),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
        )

        return Response(
            ConversationTotalsMetricsSerializer(totals).data,
            status=status.HTTP_200_OK,
        )
