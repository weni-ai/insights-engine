from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from insights.authentication.permissions import ProjectAuthQueryParamPermission


class SkillsMetricsView(APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    def get(self, request: Request) -> Response:
        return Response({"message": "Hello, world!"})
