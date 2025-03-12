import uuid
from rest_framework import serializers

from insights.projects.models import Project


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
