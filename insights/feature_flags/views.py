from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from insights.authentication.permissions import ProjectQueryParamPermission
from insights.feature_flags.integrations.growthbook.instance import (
    GROWTHBOOK_CLIENT,
)
from insights.feature_flags.serializers import (
    FeatureFlagsQueryParamsSerializer,
)
from insights.feature_flags.service import FeatureFlagService


class FeatureFlagsViewSet(GenericViewSet):
    """
    View for getting the active features for a project.
    """

    service = FeatureFlagService(growthbook_client=GROWTHBOOK_CLIENT)
    permission_classes = [IsAuthenticated, ProjectQueryParamPermission]
    serializer_class = FeatureFlagsQueryParamsSerializer

    def list(self, request, *args, **kwargs) -> Response:
        """
        Get the active features for a project.
        """

        query_params = FeatureFlagsQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        active_features = self.service.get_feature_flags_list_for_user_and_project(
            user=request.user,
            project=query_params.validated_data["project"],
        )

        return Response({"active_features": active_features}, status=status.HTTP_200_OK)
