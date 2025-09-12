from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from insights.feature_flags.integrations.growthbook.auth import (
    GrowthbookWebhookSecretAuthentication,
)
from insights.feature_flags.integrations.growthbook.tasks import (
    update_growthbook_feature_flags,
)


class GrowthbookWebhook(GenericViewSet):
    authentication_classes = [GrowthbookWebhookSecretAuthentication]

    def create(self, request, *args, **kwargs):
        update_growthbook_feature_flags.delay()
        return Response(status=status.HTTP_204_NO_CONTENT)