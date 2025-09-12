from django.urls import path
from insights.feature_flags.views import FeatureFlagCheckView

app_name = "feature_flags"

urlpatterns = [
    path("check", FeatureFlagCheckView.as_view(), name="check"),
]