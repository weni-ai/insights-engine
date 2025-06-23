from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
    NPSQueryParamsSerializer,
    NPSSerializer,
    RoomsByQueueMetricQueryParamsSerializer,
    RoomsByQueueMetricSerializer,
    SubjectsDistributionMetricsQueryParamsSerializer,
    SubjectsDistributionMetricsSerializer,
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

    @action(detail=False, methods=["get"])
    def queues(self, request: Request) -> Response:
        query_params = RoomsByQueueMetricQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        rooms_by_queue = self.service.get_rooms_numbers_by_queue(
            project=query_params.validated_data["project"],
            start_date=query_params.validated_data["start_date"],
            end_date=query_params.validated_data["end_date"],
            limit=query_params.validated_data.get("limit", None),
        )

        serializer = RoomsByQueueMetricSerializer(rooms_by_queue)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
