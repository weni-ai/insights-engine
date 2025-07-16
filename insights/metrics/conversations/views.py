from typing import TYPE_CHECKING

from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from insights.metrics.conversations.serializers import (
    CreateSubtopicSerializer,
    CreateTopicSerializer,
    DeleteTopicSerializer,
    GetSubtopicsQueryParamsSerializer,
    GetTopicsQueryParamsSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import ProjectAuth


if TYPE_CHECKING:
    from uuid import UUID
    from rest_framework.request import Request
    from insights.users.models import User


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()

    def _check_project_permission_for_user(
        self, project_uuid: "UUID", user: "User"
    ) -> bool:
        return ProjectAuth.objects.filter(
            project=project_uuid,
            user=user,
            role=1,
        ).exists()

    @action(
        detail=False,
        methods=["get", "post"],
        url_path="topics",
        url_name="topics",
        permission_classes=[IsAuthenticated],
    )
    def topics(self, request: "Request", *args, **kwargs):
        """
        Get or create conversation topics
        """
        if request.method == "GET":
            query_params = GetTopicsQueryParamsSerializer(data=request.query_params)
            query_params.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                query_params.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            topics = self.service.get_topics(
                query_params.validated_data["project_uuid"]
            )

            return Response(topics, status=status.HTTP_200_OK)
        elif request.method == "POST":
            serializer = CreateTopicSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                serializer.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            topic = self.service.create_topic(
                serializer.validated_data["project_uuid"],
                serializer.validated_data["name"],
                serializer.validated_data["description"],
            )

            return Response(topic, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get"],
        url_path="subtopics",
        url_name="subtopics",
        permission_classes=[IsAuthenticated],
    )
    def subtopics(self, request: "Request", *args, **kwargs):
        """
        Get or create conversation subtopics
        """
        if request.method == "GET":
            query_params = GetSubtopicsQueryParamsSerializer(data=request.query_params)
            query_params.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                query_params.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            subtopics = self.service.get_subtopics(
                query_params.validated_data["project_uuid"],
                query_params.validated_data["topic_uuid"],
            )

            return Response(subtopics, status=status.HTTP_200_OK)
        else:
            serializer = CreateSubtopicSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                serializer.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            subtopic = self.service.create_subtopic(
                serializer.validated_data["project_uuid"],
                serializer.validated_data["topic_uuid"],
                serializer.validated_data["name"],
                serializer.validated_data["description"],
            )

            return Response(subtopic, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["delete"],
        url_path="topics/(?P<topic_uuid>[^/.]+)",
        url_name="delete-topic",
        permission_classes=[IsAuthenticated],
    )
    def delete_topic(self, request: "Request", *args, **kwargs):
        """
        Delete a conversation topic
        """

        topic_uuid = kwargs.get("topic_uuid")

        serializer = DeleteTopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self._check_project_permission_for_user(
            serializer.validated_data["project_uuid"], request.user
        ):
            raise PermissionDenied("User does not have permission for this project")

        topic = self.service.delete_topic(
            serializer.validated_data["project_uuid"],
            topic_uuid,
        )

        return Response(topic, status=status.HTTP_204_NO_CONTENT)
