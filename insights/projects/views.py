from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from insights.authentication.permissions import IsProjectAdminPermission
from insights.projects.models import Project
from insights.projects.serializers import ProjectSerializer


class UserProjectsView(APIView):
    permission_classes = [IsAuthenticated, IsProjectAdminPermission]

    def get(self, request, *args, **kwargs):
        projects = Project.objects.filter(
            authorizations__user=request.user,
            authorizations__role=1,
        )
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=200)
