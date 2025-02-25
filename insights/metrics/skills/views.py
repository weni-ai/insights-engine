from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from sentry_sdk import capture_exception

from insights.authentication.permissions import (
    InternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
)
from insights.metrics.skills.serializers import SkillMetricsQueryParamsSerializer
from insights.metrics.skills.services.factories import SkillMetricsServiceFactory
from insights.projects.models import Project


class SkillsMetricsView(APIView):
    permission_classes = [
        IsAuthenticated,
        (ProjectAuthQueryParamPermission | InternalAuthenticationPermission),
    ]

    @extend_schema(
        parameters=[SkillMetricsQueryParamsSerializer],
        responses={status.HTTP_200_OK: dict},
    )
    def get(self, request: Request) -> Response:
        serializer = SkillMetricsQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        filters = request.query_params.copy()
        filters.pop("skill", None)
        filters.pop("project_uuid", None)

        project = get_object_or_404(
            Project, uuid=request.query_params.get("project_uuid")
        )

        try:
            service = SkillMetricsServiceFactory().get_service(
                skill_name=request.query_params.get("skill"),
                project=project,
                filters=filters,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            metrics = service.get_metrics()
        except (MissingFiltersError, InvalidDateRangeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            capture_exception(e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(metrics, status=status.HTTP_200_OK)
