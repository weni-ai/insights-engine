from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.serializers import (
    ConversationTotalsMetricsQueryParamsSerializer,
    ConversationTotalsMetricsSerializer,
    CreateTopicSerializer,
    CsatMetricsQueryParamsSerializer,
    CustomMetricsQueryParamsSerializer,
    DeleteTopicSerializer,
    GetTopicsQueryParamsSerializer,
    NpsMetricsQueryParamsSerializer,
    TopicsDistributionMetricsQueryParamsSerializer,
    TopicsDistributionMetricsSerializer,
    ConversationsSubjectsMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsQueryParamsSerializer,
    ConversationsTimeseriesMetricsSerializer,
    NPSQueryParamsSerializer,
    NPSSerializer,
    RoomsByQueueMetricQueryParamsSerializer,
    RoomsByQueueMetricSerializer,
    SubjectsMetricsSerializer,
    NpsMetricsSerializer,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import ProjectAuth


if TYPE_CHECKING:
    from uuid import UUID
    from insights.users.models import User
    from rest_framework.request import Request


class ConversationsMetricsViewSet(GenericViewSet):
    """
    ViewSet to get conversations metrics
    """

    service = ConversationsMetricsService()
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

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
            start_date=query_params.validated_data["start_date"].isoformat(),
            end_date=query_params.validated_data["end_date"].isoformat(),
            unit=query_params.validated_data["unit"],
        )

        return Response(
            ConversationsTimeseriesMetricsSerializer(data).data,
            status=status.HTTP_200_OK,
        )

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
        url_path="topics-distribution",
        url_name="topics-distribution",
        serializer_class=TopicsDistributionMetricsSerializer,
    )
    def topics_distribution(self, request: "Request") -> Response:
        """
        Get topics distribution
        """
        serializer = TopicsDistributionMetricsQueryParamsSerializer(
            data=request.query_params
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            metrics = self.service.get_topics_distribution(
                serializer.validated_data["project"],
                serializer.validated_data["start_date"].isoformat(),
                serializer.validated_data["end_date"].isoformat(),
                serializer.validated_data["type"],
            )
        except ConversationsMetricsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            TopicsDistributionMetricsSerializer(metrics).data,
            status=status.HTTP_200_OK,
        )

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

            try:
                topics = self.service.get_topics(
                    query_params.validated_data["project_uuid"]
                )
            except ConversationsMetricsError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(topics, status=status.HTTP_200_OK)
        elif request.method == "POST":
            serializer = CreateTopicSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                serializer.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            try:
                topic = self.service.create_topic(
                    serializer.validated_data["project_uuid"],
                    serializer.validated_data["name"],
                    serializer.validated_data["description"],
                )
            except ConversationsMetricsError:
                return Response(
                    {"error": "Internal server error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(topic, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["get", "post"],
        url_path="topics/(?P<topic_uuid>[^/.]+)/subtopics",
        url_name="subtopics",
        permission_classes=[IsAuthenticated],
    )
    def subtopics(self, request: "Request", *args, **kwargs):
        """
        Get or create conversation subtopics
        """
        if request.method == "GET":
            query_params = GetTopicsQueryParamsSerializer(data=request.query_params)
            query_params.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                query_params.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            topic_uuid = kwargs.get("topic_uuid")

            try:
                subtopics = self.service.get_subtopics(
                    query_params.validated_data["project_uuid"],
                    topic_uuid,
                )
            except ConversationsMetricsError:
                return Response(
                    {"error": "Internal server error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(subtopics, status=status.HTTP_200_OK)
        else:
            serializer = CreateTopicSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            if not self._check_project_permission_for_user(
                serializer.validated_data["project_uuid"], request.user
            ):
                raise PermissionDenied("User does not have permission for this project")

            try:
                topic_uuid = kwargs.get("topic_uuid")

                subtopic = self.service.create_subtopic(
                    serializer.validated_data["project_uuid"],
                    topic_uuid,
                    serializer.validated_data["name"],
                    serializer.validated_data["description"],
                )
            except ConversationsMetricsError:
                return Response(
                    {"error": "Internal server error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(subtopic, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["delete"],
        url_path="topics/(?P<topic_uuid>[^/.]+)",
        url_name="topic",
        permission_classes=[IsAuthenticated],
    )
    def topic(self, request: "Request", *args, **kwargs):
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

        try:
            self.service.delete_topic(
                serializer.validated_data["project_uuid"],
                topic_uuid,
            )
        except ConversationsMetricsError:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["delete"],
        url_path="topics/(?P<topic_uuid>[^/.]+)/subtopics/(?P<subtopic_uuid>[^/.]+)",
        url_name="subtopic",
        permission_classes=[IsAuthenticated],
    )
    def subtopic(self, request: "Request", *args, **kwargs):
        topic_uuid = kwargs.get("topic_uuid")
        subtopic_uuid = kwargs.get("subtopic_uuid")

        serializer = DeleteTopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self._check_project_permission_for_user(
            serializer.validated_data["project_uuid"], request.user
        ):
            raise PermissionDenied("User does not have permission for this project")

        try:
            self.service.delete_subtopic(
                serializer.validated_data["project_uuid"],
                topic_uuid,
                subtopic_uuid,
            )
        except ConversationsMetricsError:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        serializer_class=ConversationTotalsMetricsSerializer,
    )
    def totals(self, request: "Request", *args, **kwargs) -> Response:
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
                start_date=query_params_serializer.validated_data[
                    "start_date"
                ].isoformat(),
                end_date=query_params_serializer.validated_data["end_date"].isoformat(),
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
        url_path="csat",
        url_name="csat",
    )
    def csat_metrics(self, request) -> Response:
        """
        Get csat metrics
        """

        query_params = CsatMetricsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        try:
            csat_metrics = self.service.get_csat_metrics(
                project_uuid=query_params.validated_data["project_uuid"],
                widget=query_params.validated_data["widget"],
                start_date=query_params.validated_data["start_date"].isoformat(),
                end_date=query_params.validated_data["end_date"].isoformat(),
                metric_type=query_params.validated_data["type"],
            )
        except ConversationsMetricsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(csat_metrics, status=status.HTTP_200_OK)

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
        query_params = NpsMetricsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        try:
            nps_metrics = self.service.get_nps_metrics(
                project_uuid=query_params.validated_data["project_uuid"],
                widget=query_params.validated_data["widget"],
                start_date=query_params.validated_data["start_date"].isoformat(),
                end_date=query_params.validated_data["end_date"].isoformat(),
                metric_type=query_params.validated_data["type"],
            )
        except ConversationsMetricsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            NpsMetricsSerializer(nps_metrics).data, status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="custom",
        url_name="custom",
    )
    def custom_metrics(self, request: "Request", *args, **kwargs) -> Response:
        """
        Get custom metrics
        """
        serializer = CustomMetricsQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            metrics = self.service.get_generic_metrics_by_key(
                project_uuid=serializer.validated_data["project_uuid"],
                widget=serializer.validated_data["widget"],
                start_date=serializer.validated_data["start_date"],
                end_date=serializer.validated_data["end_date"],
            )
        except ConversationsMetricsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(metrics, status=status.HTTP_200_OK)
