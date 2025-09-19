from django.utils.translation import gettext_lazy as _


from rest_framework.views import APIView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import (
    ProjectAuthQueryParamPermission,
    ProjectAuthBodyPermission,
)
from insights.metrics.conversations.integrations.elasticsearch.services import (
    ConversationsElasticsearchService,
)
from insights.metrics.conversations.reports.services import ConversationsReportService
from insights.metrics.conversations.reports.serializers import (
    GetConversationsReportStatusQueryParamsSerializer,
    GetConversationsReportStatusResponseSerializer,
    RequestConversationsReportGenerationSerializer,
)
from insights.reports.choices import ReportStatus
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
    )

    @property
    def permission_classes(self):
        permissions = [IsAuthenticated]

        if self.request.method == "GET":
            permissions.append(ProjectAuthQueryParamPermission)

        if self.request.method == "POST":
            permissions.append(ProjectAuthBodyPermission)

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
        serializer.is_valid(raise_exception=True)

        if self.service.get_current_report_for_project(
            serializer.validated_data["project"]
        ):
            return Response(
                {"error": _("A report is already being generated for this project")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_config = serializer.validated_data.get("source_config", {})

        source_config.update(
            {
                "sections": serializer.validated_data.get("sections", []),
                "custom_widgets": serializer.validated_data.get("custom_widgets", []),
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
