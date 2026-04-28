from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from insights.projects.models import Project
from insights.projects.serializers import ProjectSerializer


class UserProjectsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.filter(
            authorizations__user=self.request.user,
            authorizations__role=1,
        )
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
