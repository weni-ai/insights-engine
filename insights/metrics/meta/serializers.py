import uuid
from rest_framework import serializers

from insights.projects.models import Project
from django.utils.translation import gettext as _

from insights.dashboards.models import Dashboard
from insights.metrics.meta.models import FavoriteTemplate
from insights.projects.models import ProjectAuth
from insights.metrics.meta.choices import (
    WhatsAppMessageTemplatesCategories,
    WhatsAppMessageTemplatesLanguages,
)


class MessageTemplatesQueryParamsSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False, default=10)
    after = serializers.CharField(required=False)
    before = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    category = serializers.ChoiceField(
        choices=WhatsAppMessageTemplatesCategories, required=False
    )
    language = serializers.ChoiceField(
        choices=WhatsAppMessageTemplatesLanguages, required=False
    )

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


class WhatsappPhoneNumberSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    display_phone_number = serializers.CharField(required=True)


class WhatsappIntegrationWebhookSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    waba_id = serializers.CharField(required=True)
    phone_number = WhatsappPhoneNumberSerializer(required=True)

    def validate_project_uuid(self, value) -> uuid.UUID:
        if not Project.objects.filter(uuid=value).exists():
            raise serializers.ValidationError(
                "Project not found", code="project_not_found"
            )

        return value


class WhatsappIntegrationWebhookRemoveSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    waba_id = serializers.CharField(required=True)

    def validate_project_uuid(self, value) -> uuid.UUID:
        if not Project.objects.filter(uuid=value).exists():
            raise serializers.ValidationError(
                "Project not found", code="project_not_found"
            )

        return value


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


class MessageTemplatesCategorySerializer(serializers.Serializer):
    value = serializers.CharField()
    name = serializers.CharField()


class MessageTemplatesCategoriesSerializer(serializers.Serializer):
    categories = MessageTemplatesCategorySerializer(many=True)


class MessageTemplatesLanguageSerializer(serializers.Serializer):
    value = serializers.CharField()
    name = serializers.CharField()


class MessageTemplatesLanguagesSerializer(serializers.Serializer):
    languages = MessageTemplatesLanguageSerializer(many=True)


class FavoriteTemplatesQueryParamsSerializer(BaseFavoriteTemplateSerializer):
    pass
