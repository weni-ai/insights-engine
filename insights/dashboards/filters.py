from django_filters import FilterSet

from insights.dashboards.models import Dashboard


class DashboardFilter(FilterSet):
    class Meta:
        model = Dashboard
        fields = ["project"]
