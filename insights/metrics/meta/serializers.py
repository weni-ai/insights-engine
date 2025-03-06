import uuid
from rest_framework import serializers

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


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
