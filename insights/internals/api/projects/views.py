from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from insights.authentication.authentication import JWTAuthentication
from insights.authentication.permissions import (
    HasInternalAuthenticationPermission,
    InternalAuthenticationPermission,
)
from insights.projects.models import Project
from insights.projects.usecases.update_vtex_account import UpdateProjectVTEXAccount

from .serializers import (
    ProjectVTEXAccountSerializer,
    UpdateProjectVTEXAccountRequestSerializer,
)


class UpdateProjectVTEXAccountView(views.APIView):
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

    def patch(self, request: Request, project_uuid: str) -> Response:
        serializer = UpdateProjectVTEXAccountRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = get_object_or_404(Project, uuid=project_uuid)

        user = getattr(request, "user", None)
        user_email = user.email if user is not None and user.is_authenticated else None

        UpdateProjectVTEXAccount().execute(
            project=project,
            vtex_account=serializer.validated_data["vtex_account"],
            user_email=user_email,
        )

        response_data = ProjectVTEXAccountSerializer(project).data

        return Response(response_data, status=status.HTTP_200_OK)
