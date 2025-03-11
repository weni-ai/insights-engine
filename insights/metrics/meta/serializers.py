from django.utils.translation import gettext as _
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.projects.models import ProjectAuth


class MessageTemplatesQueryParamsSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False, default=10)
    after = serializers.CharField(required=False)
    before = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    language = serializers.CharField(required=False)

    def validate_limit(self, value):
        max_limit = 20

        if value > max_limit:
            raise serializers.ValidationError(
                f"Limit must be less than {max_limit}", code="limit_too_large"
            )

        return value

    def validate(self, attrs):
        data = super().validate(attrs)

        if "search" in attrs:
            data["name"] = attrs.pop("search")

        return data


class BaseFavoriteTemplatesSerializer(serializers.Serializer):
    dashboard = serializers.PrimaryKeyRelatedField(queryset=Dashboard.objects.all())
    template_id = serializers.CharField()

    def _get_dashboard_queryset(self):
        user = self.context["request"].user
        project_auths = ProjectAuth.objects.filter(user=user)

        return Dashboard.objects.filter(
            project__in=project_auths.values_list("project", flat=True)
        )

    def get_fields(self):
        fields = super().get_fields()
        fields["dashboard"].queryset = self._get_dashboard_queryset()

        return fields


class AddTemplateToFavoritesSerializer(BaseFavoriteTemplatesSerializer):
    def save(self, **kwargs):
        dashboard = self.validated_data["dashboard"]
        config = dashboard.config.copy() if dashboard.config else {}

        if not config.get("favorite_templates"):
            config["favorite_templates"] = []

        config["favorite_templates"].append(self.validated_data["template_id"])

        dashboard.config = config
        dashboard.save(update_fields=["config"])

        return dashboard


class RemoveTemplateFromFavoritesSerializer(BaseFavoriteTemplatesSerializer):
    def validate(self, attrs):
        config = attrs.get("dashboard").config or {}
        favorite_templates = config.get("favorite_templates") or []

        if attrs.get("template_id") not in favorite_templates:
            raise serializers.ValidationError(
                {"template_id": [_("Template not in favorites")]},
                code="template_not_in_favorites",
            )

        return super().validate(attrs)

    def save(self, **kwargs):
        dashboard = self.validated_data["dashboard"]
        config = dashboard.config.copy() if dashboard.config else {}

        config["favorite_templates"].remove(self.validated_data["template_id"])

        dashboard.config = config
        dashboard.save(update_fields=["config"])

        return dashboard
