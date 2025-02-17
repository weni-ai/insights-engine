from django.urls import include, path
from rest_framework import routers

from insights.metrics.meta.views import WhatsAppMessageTemplatesView


namespace = "insights_metrics_meta"

router = routers.DefaultRouter()
router.register(
    r"whatsapp_message_templates",
    WhatsAppMessageTemplatesView,
    basename="whatsapp_message_templates",
)

urlpatterns = [
    path("", include(router.urls)),
]
