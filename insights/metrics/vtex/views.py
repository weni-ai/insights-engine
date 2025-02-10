from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.metrics.vtex.services.orders_service import OrdersService


class VtexOrdersViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    # TODO: add extend schema with required params
    @action(methods=["get"], detail=False)
    def utm_revenue(self, request: Request) -> Response:
        project_uuid = request.query_params.get("project_uuid", None)
        feature = request.query_params.get("feature", None)

        if not feature:
            raise ValidationError(
                {"feature": [_("This field is required.")]}, code="missing_feature"
            )

        # TODO: add dates
        filters = {
            "project_uuid": project_uuid,
            "feature": feature,
        }

        service = OrdersService(project_uuid)
        utm_revenue = service.get_utm_revenue(feature, filters)

        return Response({"utm_revenue": utm_revenue}, status=status.HTTP_200_OK)
