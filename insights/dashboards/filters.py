from django_filters import FilterSet
from django.http import QueryDict

from insights.dashboards.models import Dashboard


class DashboardFilter(FilterSet):
    class Meta:
        model = Dashboard
        fields = ["project"]
