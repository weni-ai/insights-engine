from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from insights.authentication.permissions import ProjectAuthQueryParamPermission
from insights.feature_flags.client import FeatureFlagClient
from insights.feature_flags.criteria import build_attributes


class FeatureFlagCheckView(views.APIView):
    permission_classes = [IsAuthenticated, ProjectAuthQueryParamPermission]

    def get(self, request: Request) -> Response:
        feature = request.query_params.get("feature")
        if not feature:
            return Response({"detail": "feature is required"}, status=status.HTTP_400_BAD_REQUEST)
        attributes = build_attributes(request)
        is_on = FeatureFlagClient().is_on(feature_key=feature, attributes=attributes)
        return Response({"feature": feature, "on": is_on}, status=status.HTTP_200_OK)