from django.urls import path

from insights.commerce.views import (
    AbandonedCartStatusView,
    MarketingPricingView,
)


namespace = "insights_commerce"


urlpatterns = [
    path(
        "abandoned-cart/status/",
        AbandonedCartStatusView.as_view(),
        name="abandoned-cart-status",
    ),
    path(
        "marketing-pricing/",
        MarketingPricingView.as_view(),
        name="marketing-pricing",
    ),
]
