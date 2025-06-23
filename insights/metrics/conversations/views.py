from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    NPSQueryParamsSerializer,
    NPSSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(detail=False, methods=["get"], serializer_class=NPSSerializer)
    def nps(self, request: Request, *args, **kwargs):
        """
        Get the NPS for a project
        """
        query_params = NPSQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        nps = self.service.get_nps(
            project=query_params.validated_data["project"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            type=query_params.validated_data["type"],
        )
        serializer = NPSSerializer(nps)

        return Response(serializer.data, status=status.HTTP_200_OK)
