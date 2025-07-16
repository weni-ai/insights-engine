from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
    CreateSubtopicSerializer,
    CreateTopicSerializer,
    DeleteTopicSerializer,
    GetSubtopicsQueryParamsSerializer,
    GetTopicsQueryParamsSerializer,
    NPSQueryParamsSerializer,
    NPSSerializer,
    RoomsByQueueMetricQueryParamsSerializer,
    RoomsByQueueMetricSerializer,
    SubjectsDistributionMetricsQueryParamsSerializer,
    SubjectsDistributionMetricsSerializer,
    SubjectsMetricsSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import ProjectAuth


if TYPE_CHECKING:
    from uuid import UUID
    from insights.users.models import User


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

        try:
            totals = self.service.get_totals(
                project=query_params_serializer.validated_data["project"],
                start_date=request.query_params.get("start_date"),
                end_date=request.query_params.get("end_date"),
            )
        except Exception:
            return Response(
                {"error": "Error getting conversations metrics totals"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
