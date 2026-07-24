from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import viewsets
from weni_commons.auth import WeniAuthViewMixin

from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    InternalAuthenticationPermission,
    ProjectAuthQueryParamPermission,
)
from insights.authentication.weni_auth import (
    query_params_with_auth_project_uuid,
    weni_authentication_classes,
)
from insights.metrics.vtex.serializers import (
    InternalVTEXOrdersRequestSerializer,
    UTMSourceMetricsQueryParamsSerializer,
)
from insights.metrics.vtex.usecases.utm_source_metrics import UTMSourceMetricsUseCase
from insights.projects.models import Project


class VtexOrdersViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    @action(methods=["get"], detail=False)
    def from_utm_source(self, request: Request) -> Response:
        serializer = UTMSourceMetricsQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        project = get_object_or_404(Project, uuid=validated["project_uuid"])

        use_case = UTMSourceMetricsUseCase()
        status_code, response_data = use_case.execute(
            project,
            validated["utm_source"],
            validated["start_date"],
            validated["end_date"],
        )

        return Response(response_data, status=status_code)


class InternalVTEXOrdersViewSet(WeniAuthViewMixin, viewsets.ViewSet):
    permission_classes = [
        HasInternalAuthenticationPermission
        | (IsAuthenticated & InternalAuthenticationPermission)
    ]

    @property
    def authentication_classes(self):
        return weni_authentication_classes(super().authentication_classes)

    @action(methods=["get"], detail=False)
    def from_utm_source(self, request: Request) -> Response:
        serializer = InternalVTEXOrdersRequestSerializer(
            data=query_params_with_auth_project_uuid(request)
        )
        serializer.is_valid(raise_exception=True)

        project = get_object_or_404(Project, uuid=self.auth.project_uuid)

        validated = serializer.validated_data
        use_case = UTMSourceMetricsUseCase()
        status_code, response_data = use_case.execute(
            project,
            validated["utm_source"],
            validated["start_date"],
            validated["end_date"],
        )

        return Response(response_data, status=status_code)
