from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from insights.authentication.authentication import JWTAuthentication
from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    InternalAuthenticationPermission,
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

        project = get_object_or_404(Project, uuid=project_uuid)
        project_tz = ZoneInfo(project.timezone) if project.timezone else ZoneInfo("UTC")

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

        start_date = start_date.replace(tzinfo=project_tz).astimezone(timezone.utc)
        end_date = end_date.replace(
            hour=23, minute=59, second=59, tzinfo=project_tz
        ).astimezone(timezone.utc)

        filters = {
            "project_uuid": project_uuid,
            "start_date": start_date,
            "end_date": end_date,
        }
        service = OrdersService(project)
        response_data = service.get_metrics_from_utm_source(utm_source, filters)

        return Response(response_data, status=status.HTTP_200_OK)


class InternalVTEXOrdersViewSet(viewsets.ViewSet):
    permission_classes = [
        HasInternalAuthenticationPermission
        | (IsAuthenticated & InternalAuthenticationPermission)
    ]

    @property
    def authentication_classes(self):
        # Try JWT first so Bearer JWT tokens are accepted before OIDC (which would raise on invalid OIDC token)
        classes = list(super().authentication_classes)
        if JWTAuthentication not in classes:
            classes.insert(0, JWTAuthentication)
        return classes

    @action(methods=["get"], detail=False)
    def from_utm_source(self, request: Request) -> Response:
        serializer = InternalVTEXOrdersRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if not (project_uuid := getattr(request, "project_uuid", None)):
            project_uuid = serializer.validated_data["project_uuid"]

        project_uuid = str(project_uuid)
        project = get_object_or_404(Project, uuid=project_uuid)
        project_tz = ZoneInfo(project.timezone) if project.timezone else ZoneInfo("UTC")

        utm_source = serializer.validated_data.get("utm_source", None)
        start_date_str = serializer.data.get("start_date", None)
        end_date_str = serializer.data.get("end_date", None)

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d")
            .replace(tzinfo=project_tz)
            .astimezone(timezone.utc)
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d")
            .replace(hour=23, minute=59, second=59, tzinfo=project_tz)
            .astimezone(timezone.utc)
        )

        filters = {
            "project_uuid": project_uuid,
            "start_date": start_date,
            "end_date": end_date,
        }

        service = OrdersService(project)
        response_data = service.get_metrics_from_utm_source(utm_source, filters)

        return Response(response_data, status=status.HTTP_200_OK)
