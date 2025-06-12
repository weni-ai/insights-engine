from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
    SubjectsMetricsSerializer,
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
            project=query_params_serializer.validated_data["project"],
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
        )

        return Response(
            ConversationTotalsMetricsSerializer(totals).data,
            status=status.HTTP_200_OK,
        )

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
        data = self.service.get_timeseries(
            project=query_params.validated_data["project"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            unit=query_params.validated_data["unit"],
        )

        return Response(self.serializer_class(data).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], serializer_class=SubjectsMetricsSerializer)
    def subjects(self, request: Request) -> Response:
        query_params = ConversationsSubjectsMetricsQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)

        subjects_metrics = self.service.get_subjects_metrics(
            project_uuid=query_params.validated_data["project_uuid"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            conversation_type=query_params.validated_data["type"],
            limit=query_params.validated_data.get("limit", None),
        )

        return Response(
            SubjectsMetricsSerializer(subjects_metrics).data,
            status=status.HTTP_200_OK,
        )
