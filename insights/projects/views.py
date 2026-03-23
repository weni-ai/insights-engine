from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from insights.projects.models import Project
from insights.projects.serializers import ProjectSerializer


class UserProjectsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(
            authorizations__user=self.request.user,
            authorizations__role=1,
        )
