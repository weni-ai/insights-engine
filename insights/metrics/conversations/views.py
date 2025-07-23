from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import CsatMetricsQueryParamsSerializer
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
        url_path="csat-metrics",
        url_name="csat-metrics",
    )
    def csat_metrics(self, request) -> Response:
        """
        Get csat metrics
        """

        query_params = CsatMetricsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        csat_metrics = self.service.get_csat_metrics(
            project_uuid=query_params.validated_data["project_uuid"],
            widget=query_params.validated_data["widget"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            metric_type=query_params.validated_data["type"],
        )

        return Response(csat_metrics, status=status.HTTP_200_OK)
