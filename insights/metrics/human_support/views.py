from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.human_support.services import HumanSupportDashboardService
from insights.projects.models import Project


class DetailedMonitoringOnGoingView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    feature_flag_key = "human-support-detailed-monitoring"

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = {key: value for key, value in request.query_params.items()}
        data = service.get_detailed_monitoring_on_going(filters=filters)
        return Response(data, status=200)


class DetailedMonitoringAwaitingView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    feature_flag_key = "human-support-detailed-monitoring"

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = {key: value for key, value in request.query_params.items()}
        data = service.get_detailed_monitoring_awaiting(filters=filters)
        return Response(data, status=200)


class DetailedMonitoringAgentsView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    feature_flag_key = "human-support-detailed-monitoring"

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = {key: value for key, value in request.query_params.items()}
        filters["user_request"] = request.user.email
        data = service.get_detailed_monitoring_agents(filters=filters)

        results = data.get("results", [])
        paginator = LimitOffsetPagination()
        paginated_results = paginator.paginate_queryset(results, request)

        return paginator.get_paginated_response(paginated_results)


class DetailedMonitoringStatusView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    feature_flag_key = "human-support-detailed-monitoring"

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = {key: value for key, value in request.query_params.items()}
        filters["user_request"] = request.user.email
        data = service.get_detailed_monitoring_status(filters=filters)

        results = data.get("results", [])
        paginator = LimitOffsetPagination()
        paginated_results = paginator.paginate_queryset(results, request)

        return paginator.get_paginated_response(paginated_results)
