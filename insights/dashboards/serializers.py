from rest_framework import serializers

from insights.dashboards.models import Dashboard


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["uuid", "name", "is_default", "grid"]
