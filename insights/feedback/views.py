from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _

from insights.dashboards.models import Dashboard
from insights.feedback.serializers.views_serializers import (
    CheckSurveyQueryParamsSerializer,
    CheckSurveyResponseSerializer,
)
from insights.feedback.services import FeedbackService


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
