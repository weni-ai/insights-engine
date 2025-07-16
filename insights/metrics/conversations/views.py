from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import GetSubtopicsQueryParamsSerializer
from insights.metrics.conversations.services import ConversationsMetricsService


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(detail=False, methods=["get"], url_path="topics", url_name="topics")
    def get_topics(self, request: Request, *args, **kwargs):
        """
        Get conversation topics
        """
        topics = self.service.get_topics(request.query_params.get("project_uuid"))

        return Response(topics, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="subtopics", url_name="subtopics")
    def get_subtopics(self, request: Request, *args, **kwargs):
        """
        Get conversation subtopics
        """

        query_params = GetSubtopicsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        subtopics = self.service.get_subtopics(
            query_params.validated_data["project_uuid"],
            query_params.validated_data["topic_uuid"],
        )

        return Response(subtopics, status=status.HTTP_200_OK)
