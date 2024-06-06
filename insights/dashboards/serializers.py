from django.conf import settings
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.widgets.models import Report, Widget


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["uuid", "name", "is_default", "grid"]


class DashboardIsDefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["is_default"]


class ReportSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.config.get("external_url"):
            return obj.config["external_url"]
        return f"{settings.INSIGHTS_DOMAIN}/dashboards/{obj.widget.dashboard.uuid}/widgets/{obj.widget.uuid}/report/"

    class Meta:
        model = Report
        fields = "__all__"


class DashboardWidgetsSerializer(serializers.ModelSerializer):
    report = ReportSerializer()

    class Meta:
        model = Widget
        fields = "__all__"
