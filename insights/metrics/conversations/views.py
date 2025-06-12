from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
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
        serializer_class=ConversationsTimeseriesMetricsSerializer,
    )
    def timeseries(self, request: Request, *args, **kwargs) -> Response:
        """
        Get conversations timeseries metrics
        """
        query_params = ConversationsTimeseriesMetricsQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        data = self.service.get_timeseries(**query_params.validated_data)

        return Response(data, status=status.HTTP_200_OK)
