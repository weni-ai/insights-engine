from rest_framework import serializers

from insights.projects.models import Project


class ConversationBaseQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for conversation base query params
    """

    start_date = serializers.DateField()
    end_date = serializers.DateField()
    project_uuid = serializers.UUIDField()

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"start_date": "Start date must be before end date"},
                code="start_date_after_end_date",
            )

        project = Project.objects.filter(uuid=attrs["project_uuid"]).first()

        if not project:
            raise serializers.ValidationError(
                {"project_uuid": "Project not found"}, code="project_not_found"
            )

        attrs["project"] = project

        return attrs


class GetTopicsQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for getting conversation topics
    """

    project_uuid = serializers.UUIDField(required=True)


class BaseTopicSerializer(serializers.Serializer):
    """
    Serializer for conversation topic
    """

    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class CreateTopicSerializer(BaseTopicSerializer):
    """
    Serializer for creating a conversation topic
    """

    project_uuid = serializers.UUIDField(required=True)


class DeleteTopicSerializer(serializers.Serializer):
    """
    Serializer for deleting a conversation topic
    """

    project_uuid = serializers.UUIDField(required=True)
