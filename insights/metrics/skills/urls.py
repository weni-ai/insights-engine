from django.urls import path

from insights.metrics.skills.views import SkillsMetricsView


namespace = "insights_metrics_skills"

urlpatterns = [
    path("", SkillsMetricsView.as_view(), name="skills"),
]
