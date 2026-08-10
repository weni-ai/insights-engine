from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from weni_commons.auth import WeniAuthViewMixin

from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    InternalAuthenticationPermission,
)
from insights.authentication.weni_auth import weni_authentication_classes
from insights.projects.models import Project
from insights.projects.usecases.update_vtex_account import UpdateProjectVTEXAccount

from .serializers import (
    ProjectVTEXAccountSerializer,
    UpdateProjectVTEXAccountRequestSerializer,
)


class UpdateProjectVTEXAccountView(WeniAuthViewMixin, views.APIView):
    permission_classes = [
        HasInternalAuthenticationPermission
        | (IsAuthenticated & InternalAuthenticationPermission)
    ]

    @property
    def authentication_classes(self):
        return weni_authentication_classes(super().authentication_classes)

    def patch(self, request: Request, project_uuid: str) -> Response:
        serializer = UpdateProjectVTEXAccountRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Tenant comes from auth context (JWT claim or Keycloak resolver), never
        # from a client-controlled path segment alone.
        project = get_object_or_404(Project, uuid=self.auth.project_uuid)

        user_email = self.user_email

        project, projects_unlinked = UpdateProjectVTEXAccount().execute(
            project=project,
            vtex_account=serializer.validated_data["vtex_account"],
            user_email=user_email,
        )

        response_data = ProjectVTEXAccountSerializer(
            project,
            context={"projects_unlinked": projects_unlinked},
        ).data

        return Response(response_data, status=status.HTTP_200_OK)
