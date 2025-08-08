from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
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

    def validate_is_default(self, value: bool) -> bool:
        """
        Validates that a default dashboard cannot be set as non-default.

        Raises a ValidationError if attempting to set a default dashboard to False.
        """
        if value is False and self.instance.is_default is True:
            raise serializers.ValidationError(
                _("Cannot set a default dashboard as non-default"),
                code="cannot_set_default_dashboard_as_non_default",
            )

        return value

    @transaction.atomic
    def save(self, **kwargs):
        # If the dashboard is being set to default, we need to make sure that no other dashboard is default
        # to avoid integrity errors, as there is a unique constraint on the project and is_default fields
        if self.validated_data["is_default"] is True:
            Dashboard.objects.filter(
                project=self.instance.project, is_default=True
            ).update(is_default=False)

        if self.instance.is_default == self.validated_data["is_default"]:
            return self.instance

        instance: Dashboard = self.instance
        instance.is_default = self.validated_data["is_default"]
        instance.save(update_fields=["is_default"])

        return instance


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

    def validate_config(self, value: dict) -> dict:
        if value.get("is_whatsapp_integration") or value.get("waba_id"):
            raise serializers.ValidationError(
                "WhatsApp integration cannot be edited in dashboard config",
                code="whatsapp_integration_cannot_be_edited",
            )

        return value
