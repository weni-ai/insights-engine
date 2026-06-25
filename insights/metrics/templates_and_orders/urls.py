from django.urls import path

from insights.metrics.templates_and_orders.views import (
    InternalTemplatesAndOrdersMetricsView,
)

namespace = "insights_metrics_templates_and_orders"

urlpatterns = [
    path(
        "",
        InternalTemplatesAndOrdersMetricsView.as_view(),
        name="internal-templates-and-orders",
    ),
]
