from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from insights.authentication.authentication import JWTAuthentication
from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.metrics.vtex.serializers import InternalVTEXOrdersRequestSerializer
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project


class VtexOrdersViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(methods=["get"], detail=False)
    def from_utm_source(self, request: Request) -> Response:
        project_uuid = request.query_params.get("project_uuid", None)

        missing_fields = {}

        for field in ("utm_source", "start_date", "end_date"):
            if not request.query_params.get(field):
                missing_fields[field] = [_("Required")]

        if missing_fields:
            raise ValidationError(
                missing_fields,
                code="required",
            )

        utm_source = request.query_params.get("utm_source", None)
        start_date_str = request.query_params.get("start_date", None)
        end_date_str = request.query_params.get("end_date", None)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError as e:
            raise ValidationError(
                {"detail": [_("Invalid date format. Use YYYY-MM-DD.")]},
                code="invalid_date_format",
            ) from e

        start_date = timezone.make_aware(start_date)
        end_date = timezone.make_aware(end_date)

        filters = {
            "project_uuid": project_uuid,
            "start_date": start_date,
            "end_date": end_date,
        }

        project = get_object_or_404(Project, uuid=project_uuid)
        service = OrdersService(project)
        response_data = service.get_metrics_from_utm_source(utm_source, filters)

        return Response(response_data, status=status.HTTP_200_OK)


class InternalVTEXOrdersViewSet(viewsets.ViewSet):
    permission_classes = [HasInternalAuthenticationPermission]
    authentication_classes = [JWTAuthentication]

    @action(methods=["get"], detail=False)
    def from_utm_source(self, request: Request) -> Response:
        project_uuid = request.project_uuid

        serializer = InternalVTEXOrdersRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        utm_source = serializer.validated_data.get("utm_source", None)
        start_date_str = serializer.data.get("start_date", None)
        end_date_str = serializer.data.get("end_date", None)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        start_date = timezone.make_aware(start_date)
        end_date = timezone.make_aware(end_date)

        filters = {
            "project_uuid": project_uuid,
            "start_date": start_date,
            "end_date": end_date,
        }

        project = get_object_or_404(Project, uuid=project_uuid)
        service = OrdersService(project)
        response_data = service.get_metrics_from_utm_source(utm_source, filters)

        return Response(response_data, status=status.HTTP_200_OK)
