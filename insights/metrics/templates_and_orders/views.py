import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from weni_commons.auth import WeniAuthViewMixin

from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    InternalAuthenticationPermission,
)
from insights.authentication.weni_auth import (
    query_params_with_auth_project_uuid,
    weni_authentication_classes,
)
from insights.metrics.templates_and_orders.exceptions import (
    ErrorGettingOrdersMetrics,
)
from insights.metrics.templates_and_orders.serializers import (
    TemplatesAndOrdersQueryParamsSerializer,
)
from insights.metrics.templates_and_orders.usecases.format_templates_and_orders_response import (
    FormatTemplatesAndOrdersResponse,
)
from insights.metrics.templates_and_orders.usecases.get_templates_and_orders_metrics import (
    GetTemplatesAndOrdersMetrics,
)
from insights.projects.models import Project

logger = logging.getLogger(__name__)


class InternalTemplatesAndOrdersMetricsView(WeniAuthViewMixin, APIView):
    permission_classes = [
        HasInternalAuthenticationPermission
        | (IsAuthenticated & InternalAuthenticationPermission)
    ]

    @property
    def authentication_classes(self):
        return weni_authentication_classes(super().authentication_classes)

    def get(self, request: Request) -> Response:
        serializer = TemplatesAndOrdersQueryParamsSerializer(
            data=query_params_with_auth_project_uuid(request)
        )
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        project = get_object_or_404(Project, uuid=self.auth.project_uuid)

        get_metrics = GetTemplatesAndOrdersMetrics()
        format_response = FormatTemplatesAndOrdersResponse()

        try:
            raw_metrics = get_metrics.execute(
                project=project,
                start_date=validated["start_date"],
                end_date=validated["end_date"],
                utm_source=validated["utm_source"],
                template_name_prefix=validated["template_name_prefix"],
            )
        except ErrorGettingOrdersMetrics as e:
            logger.error("Error getting orders metrics: %s", e, exc_info=True)
            return Response(
                {"error": "Failed to retrieve orders metrics"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            capture_exception(e)
            logger.error(
                "Unexpected error getting templates and orders metrics: %s",
                e,
                exc_info=True,
            )
            return Response(
                {"error": "Failed to calculate templates and orders metrics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            format_response.execute(raw_metrics), status=status.HTTP_200_OK
        )
