from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.human_support.services import HumanSupportDashboardService
from insights.projects.models import Project
from insights.core.filters import get_filters_from_query_params


class DetailedMonitoringAgentsViewV2(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]
    feature_flag_key = "human-support-detailed-monitoring"

    def get(self, request, *args, **kwargs):
        project_uuid = request.query_params.get("project_uuid")
        if not project_uuid:
            return Response({"detail": "project_uuid is required"}, status=400)

        project = get_object_or_404(Project, uuid=project_uuid)
        service = HumanSupportDashboardService(project=project)

        filters = get_filters_from_query_params(request.query_params)
        filters["user_request"] = request.user.email
        data = service.get_detailed_monitoring_agents(filters=filters)

        return Response(data, status=200)
