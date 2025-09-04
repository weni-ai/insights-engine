from rest_framework.views import APIView

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.reports.services import ConversationsReportService
from insights.metrics.conversations.reports.serializers import (
    GetConversationsReportStatusQueryParamsSerializer,
)


class ConversationsReportsViewSet(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    service = ConversationsReportService()

    def get(self, request: Request) -> Response:
        query_params = GetConversationsReportStatusQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
