from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.api.mixins import (
    ConversationsMetricsResponseMixin,
)
from insights.metrics.conversations.api.v2.serializers import (
    NpsMetricsQueryParamsSerializerV2,
    NpsMetricsSerializerV2,
)


class ConversationsMetricsViewSetV2(
    ConversationsMetricsResponseMixin,
    ConversationsMetricsServiceResolverMixin,
    GenericViewSet,
):
    """
    ViewSet to get conversations metrics
    """

    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(
        detail=False,
        methods=["get"],
        url_path="nps",
        url_name="nps",
    )
    def nps_metrics(self, request) -> Response:
        """
        Get nps metrics
        """
        query_params = NpsMetricsQueryParamsSerializerV2(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        kwargs = {
            "project_uuid": query_params.validated_data["project_uuid"],
            "widget": query_params.validated_data["widget"],
            "start_date": query_params.validated_data["start_date"].isoformat(),
            "end_date": query_params.validated_data["end_date"].isoformat(),
            "metric_type": query_params.validated_data["type"],
        }

        response = self.prepare_metrics_response(
            self.service.get_nps_metrics,
            NpsMetricsSerializerV2,
            kwargs,
        )

        return response
