from django.conf import settings
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.widgets.models import Report, Widget


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = [
            "uuid",
            "name",
            "is_default",
            "grid",
            "is_deletable",
            "is_editable",
            "config",
        ]


class DashboardIsDefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["is_default"]


class DashboardReportSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_url(self, obj):
        config = obj.config

        if isinstance(config, dict):
            if config.get("external_url"):
                return config["external_url"]
            return f"{settings.INSIGHTS_DOMAIN}/v1/dashboards/{obj.widget.dashboard.uuid}/widgets/{obj.widget.uuid}/report/"
        elif isinstance(config, list):
            for item in config:
                if isinstance(item, dict) and item.get("external_url"):
                    return item["external_url"]
            return f"{settings.INSIGHTS_DOMAIN}/v1/dashboards/{obj.widget.dashboard.uuid}/widgets/{obj.widget.uuid}/report/"

    def get_type(self, obj):
        config = obj.config

        if isinstance(config, dict) and config.get("external_url"):
            return "external"

        elif isinstance(config, list):
            for item in config:
                if isinstance(item, dict) and item.get("external_url"):
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
    is_configurable = serializers.BooleanField(read_only=True)
    report = DashboardReportSerializer()

    class Meta:
        model = Widget
        fields = "__all__"


class DashboardEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["name", "config"]
