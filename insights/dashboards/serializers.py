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


class DashboardReportSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.config.get("external_url"):
            return obj.config["external_url"]
        return f"{settings.INSIGHTS_DOMAIN}/v1/dashboards/{obj.widget.dashboard.uuid}/widgets/{obj.widget.uuid}/report/"

    def get_type(self, obj):
        if obj.config.get("external_url"):
            return "external"
        return "internal"

    class Meta:
        model = Report
        fields = ["url", "type"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


class DashboardWidgetsSerializer(serializers.ModelSerializer):
    report = DashboardReportSerializer()

    class Meta:
        model = Widget
        fields = "__all__"
