from django.urls import include, path
from rest_framework import routers

from insights.metrics.meta.views import (
    WhatsAppMessageTemplatesView,
    WhatsappIntegrationWebhookView,
)


namespace = "insights_metrics_meta"

router = routers.DefaultRouter()
router.register(
    r"whatsapp-message-templates",
    WhatsAppMessageTemplatesView,
    basename="whatsapp-message-templates",
)

urlpatterns = [
    path(
        "internal/whatsapp-integration/",
        WhatsappIntegrationWebhookView.as_view(),
        name="whatsapp-integration",
    ),
    path("", include(router.urls)),
]
