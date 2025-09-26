from __future__ import annotations

from typing import Any, Dict

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from insights.authentication.permissions import ProjectAuthPermission
from insights.human_support.services import HumanSupportDashboardService
from insights.projects.models import Project


class DetailedMonitoringOnGoingView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        data = service.get_detailed_monitoring_on_going(filters=request.query_params)
        return Response(data, status=200)

class DetailedMonitoringAwaitingView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        data = service.get_detailed_monitoring_awaiting(filters=request.query_params)
        return Response(data, status=200)

class DetailedMonitoringAgentsView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = request.query_params.copy()
        filters["user_request"] = request.user.email
        data = service.get_detailed_monitoring_agents(filters=filters)
        return Response(data, status=200)

class DetailedMonitoringStatusView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthPermission]

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        data = service.get_detailed_monitoring_status(filters=request.query_params)
        return Response(data, status=200)