import logging

from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from sentry_sdk import capture_exception

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.commerce.exceptions import BillingRequestError
from insights.commerce.serializers import (
    AbandonedCartStatusResponseSerializer,
    MarketingPricingResponseSerializer,
)
from insights.commerce.services import (
    AbandonedCartStatusService,
    MarketingPricingService,
)

logger = logging.getLogger(__name__)


PROJECT_UUID_PARAM = OpenApiParameter(
    name="project_uuid",
    type=str,
    location=OpenApiParameter.QUERY,
    required=True,
    description="UUID of the project",
)


STUB_ABANDONED_CART_STATUS_RESPONSE = {"active": True}
STUB_MARKETING_PRICING_RESPONSE = {"value": 0.4, "currency": "BRL"}


class AbandonedCartStatusView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @extend_schema(
        parameters=[PROJECT_UUID_PARAM],
        responses={status.HTTP_200_OK: AbandonedCartStatusResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        if settings.COMMERCE_USE_STUB_RESPONSES:
            return Response(
                STUB_ABANDONED_CART_STATUS_RESPONSE,
                status=status.HTTP_200_OK,
            )

        project_uuid = request.query_params.get("project_uuid")

        service = AbandonedCartStatusService()
        active = service.is_active(project_uuid)

        return Response({"active": active}, status=status.HTTP_200_OK)


class MarketingPricingView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @extend_schema(
        parameters=[PROJECT_UUID_PARAM],
        responses={status.HTTP_200_OK: MarketingPricingResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        if settings.COMMERCE_USE_STUB_RESPONSES:
            return Response(
                STUB_MARKETING_PRICING_RESPONSE,
                status=status.HTTP_200_OK,
            )

        project_uuid = request.query_params.get("project_uuid")

        service = MarketingPricingService()

        try:
            data = service.get_marketing_pricing(project_uuid)
        except BillingRequestError as err:
            capture_exception(err)
            logger.error(
                "Error fetching marketing pricing for project %s: %s",
                project_uuid,
                err,
            )
            return Response(
                {"error": "Could not retrieve marketing pricing"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(data, status=status.HTTP_200_OK)
