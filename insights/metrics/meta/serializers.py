from typing import Literal
from django.utils.translation import gettext as _
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.metrics.meta.models import FavoriteTemplate
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


class BaseFavoriteTemplateSerializer(serializers.Serializer):
    dashboard = serializers.PrimaryKeyRelatedField(queryset=Dashboard.objects.all())

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


class BaseFavoriteTemplateOperationSerializer(BaseFavoriteTemplateSerializer):
    template_id = serializers.CharField()


class AddTemplateToFavoritesSerializer(BaseFavoriteTemplateOperationSerializer):
    def validate(self, attrs):
        if FavoriteTemplate.objects.filter(
            dashboard=attrs.get("dashboard"),
            template_id=attrs.get("template_id"),
        ).exists():
            raise serializers.ValidationError(
                {"template_id": [_("Template already in favorites")]},
                code="template_already_in_favorites",
            )

        return super().validate(attrs)

    def save(self, **kwargs):
        name = self.context["template_name"]

        return FavoriteTemplate.objects.create(
            dashboard=self.validated_data["dashboard"],
            template_id=self.validated_data["template_id"],
            name=name,
        )


class RemoveTemplateFromFavoritesSerializer(BaseFavoriteTemplateOperationSerializer):
    def validate(self, attrs):
        if not FavoriteTemplate.objects.filter(
            dashboard=attrs.get("dashboard"),
            template_id=attrs.get("template_id"),
        ).exists():
            raise serializers.ValidationError(
                {"template_id": [_("Template not in favorites")]},
                code="template_not_in_favorites",
            )
        return super().validate(attrs)

    def save(self, **kwargs):
        return FavoriteTemplate.objects.filter(
            dashboard=self.validated_data["dashboard"],
            template_id=self.validated_data["template_id"],
        ).delete()


class FavoriteTemplatesSerializer(serializers.ModelSerializer):
    waba_id = serializers.SerializerMethodField()
    project_uuid = serializers.UUIDField(
        source="dashboard.project.uuid", read_only=True
    )

    class Meta:
        model = FavoriteTemplate
        fields = ["template_id", "name", "waba_id", "project_uuid"]

    def get_waba_id(self, obj: FavoriteTemplate) -> str:
        config = obj.dashboard.config or {}

        return config.get("waba_id")


class FavoriteTemplatesQueryParamsSerializer(BaseFavoriteTemplateSerializer):
    pass
