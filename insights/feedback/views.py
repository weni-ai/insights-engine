from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from sentry_sdk import capture_exception
import logging

from insights.dashboards.models import Dashboard
from insights.feedback.models import Survey
from insights.feedback.serializers.views_serializers import (
    CheckSurveyQueryParamsSerializer,
    CheckSurveyResponseSerializer,
    CreateFeedbackResponseSerializer,
    CreateFeedbackSerializer,
)
from insights.feedback.services import FeedbackService


logger = logging.getLogger(__name__)


class FeedbackViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    service = FeedbackService()

    @action(detail=False, methods=["get"], url_path="check-survey")
    def check_survey(self, request) -> Response:
        query_params = CheckSurveyQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        dashboard = Dashboard.objects.filter(
            uuid=query_params.validated_data["dashboard"],
            project_id=query_params.validated_data["project_uuid"],
        ).first()

        if not dashboard:
            return Response(
                {"error": _("Dashboard not found")}, status=status.HTTP_404_NOT_FOUND
            )

        if not dashboard.project.authorizations.filter(
            user=request.user, role=1
        ).exists():
            return Response(
                {
                    "error": _(
                        "User does not have permission to access this dashboard's survey status"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        survey_status = self.service.get_survey_status(
            user=request.user,
            dashboard=dashboard,
        )

        return Response(
            CheckSurveyResponseSerializer(survey_status).data, status=status.HTTP_200_OK
        )

    def create(self, request: Request) -> Response:
        serializer = CreateFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dashboard = Dashboard.objects.filter(
            uuid=serializer.validated_data["dashboard"],
        ).first()

        if not dashboard:
            return Response(
                {"error": _("Dashboard not found")}, status=status.HTTP_404_NOT_FOUND
            )

        if not dashboard.project.authorizations.filter(
            user=request.user, role=1
        ).exists():
            return Response(
                {"error": _("User does not have permission to access this dashboard")},
                status=status.HTTP_403_FORBIDDEN,
            )

        survey = Survey.objects.filter(
            uuid=serializer.validated_data["survey"],
        ).first()

        if not survey:
            return Response(
                {"error": _("Survey not found")}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            feedback = self.service.create_feedback(
                user=request.user,
                dashboard=dashboard,
                survey=survey,
                dashboard_type=serializer.validated_data["type"],
                data=serializer.validated_data,
            )
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            raise e
        except Exception as e:
            event_id = capture_exception(e)
            logger.error(e)
            return Response(
                {
                    "error": _(
                        "An unexpected error occurred. Event ID: {event_id}"
                    ).format(event_id=event_id)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = CreateFeedbackResponseSerializer(feedback)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
