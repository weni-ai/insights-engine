from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from insights.authentication.permissions import ProjectQueryParamPermission
from insights.feature_flags.serializers import (
    FeatureFlagsQueryParamsSerializer,
)
from weni_feature_flags.services import FeatureFlagsService


class FeatureFlagsViewSet(GenericViewSet):
    """
    View for getting the active features for a project.
    """

    service = FeatureFlagsService()
    permission_classes = [IsAuthenticated, ProjectQueryParamPermission]
    serializer_class = FeatureFlagsQueryParamsSerializer

    def list(self, request, *args, **kwargs) -> Response:
        """
        Get the active features for a project.
        """

        query_params = FeatureFlagsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        attributes = {
            "userEmail": request.user.email,
            "projectUUID": query_params.validated_data["project"].uuid,
        }

        active_features = self.service.get_active_feature_flags_for_attributes(
            attributes=attributes,
        )

        return Response({"active_features": active_features}, status=status.HTTP_200_OK)
