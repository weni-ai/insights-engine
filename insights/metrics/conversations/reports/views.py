from django.utils.translation import gettext_lazy as _


from rest_framework.views import APIView
from rest_framework import status, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.reports.permissions import (
    CanGenerateConversationsReportPermission,
    CanCheckReportGenerationStatusPermission,
)
from insights.metrics.conversations.reports.services import ConversationsReportService
from insights.metrics.conversations.reports.serializers import (
    AvailableReportWidgetsQueryParamsSerializer,
    AvailableReportWidgetsResponseSerializer,
    GetConversationsReportStatusQueryParamsSerializer,
    GetConversationsReportStatusResponseSerializer,
    RequestConversationsReportGenerationSerializer,
)
from insights.reports.choices import ReportStatus
from insights.sources.cache import CacheClient
from insights.sources.dl_events.clients import DataLakeEventsClient
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.integrations.elasticsearch.tests.mock import (
    MockElasticsearchClient,
)


class ConversationsReportsViewSet(APIView):
    service = ConversationsReportService(
        elasticsearch_service=ConversationsElasticsearchService(
            client=MockElasticsearchClient(),
        ),
        datalake_events_client=DataLakeEventsClient(),
        metrics_service=ConversationsMetricsService(),
        cache_client=CacheClient(),
    )

    @property
    def permission_classes(self):
        permissions = [IsAuthenticated]

        if self.request.method == "GET":
            permissions.append(CanCheckReportGenerationStatusPermission)

        if self.request.method == "POST":
            permissions.append(CanGenerateConversationsReportPermission)

        return permissions

    def get(self, request: Request) -> Response:
        query_params = GetConversationsReportStatusQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)

        report = self.service.get_current_report_for_project(
            query_params.validated_data["project"]
        )

        response_body = (
            GetConversationsReportStatusResponseSerializer(instance=report).data
            if report
            else {"status": ReportStatus.READY}
        )

        return Response(response_body)

    def post(self, request: Request) -> Response:
        serializer = RequestConversationsReportGenerationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            if e.errors.get("error"):
                error = e.errors.get("error")

                if isinstance(error, list):
                    error = error[0]

                return Response(
                    {"error": error},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    e.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if self.service.get_current_report_for_project(
            serializer.validated_data["project"]
        ):
            return Response(
                {
                    "concurrent_report": _(
                        "There is another report being processed for this project"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_config = serializer.validated_data.get("source_config", {})

        source_config.update(
            {
                "sections": serializer.validated_data.get("sections", []),
                "custom_widgets": [
                    str(widget_uuid)
                    for widget_uuid in serializer.validated_data.get(
                        "custom_widgets", []
                    )
                ],
            }
        )

        filters = {
            "start": serializer.validated_data["start"],
            "end": serializer.validated_data["end"],
        }

        report = self.service.request_generation(
            project=serializer.validated_data["project"],
            source_config=source_config,
            filters=filters,
            report_format=serializer.validated_data["type"],
            requested_by=request.user,
        )

        return Response(
            GetConversationsReportStatusResponseSerializer(instance=report).data,
            status=status.HTTP_202_ACCEPTED,
        )


class AvailableWidgetsViewSet(APIView):
    service = ConversationsReportService(
        elasticsearch_service=ConversationsElasticsearchService(
            client=MockElasticsearchClient(),
        ),
        datalake_events_client=DataLakeEventsClient(),
        metrics_service=ConversationsMetricsService(),
        cache_client=CacheClient(),
    )

    permission_classes = [IsAuthenticated, CanCheckReportGenerationStatusPermission]

    def get(self, request: Request) -> Response:
        query_params = AvailableReportWidgetsQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        widgets = self.service.get_available_widgets(
            project=query_params.validated_data["project"]
        )

        return Response(AvailableReportWidgetsResponseSerializer(instance=widgets).data)
