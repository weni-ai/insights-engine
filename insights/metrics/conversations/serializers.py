from rest_framework import serializers

from insights.metrics.conversations.enums import ConversationType
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


class TopicsDistributionMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for topics distribution metrics query params
    """

    type = serializers.ChoiceField(
        choices=ConversationType.choices,
        required=True,
    )


class SubtopicSerializer(serializers.Serializer):
    """
    Serializer for subtopic
    """

    uuid = serializers.UUIDField()
    name = serializers.CharField()
    percentage = serializers.FloatField()


class TopicSerializer(serializers.Serializer):
    """
    Serializer for topic
    """

    uuid = serializers.UUIDField()
    name = serializers.CharField()
    percentage = serializers.FloatField()
    subtopics = SubtopicSerializer(many=True)


class TopicsDistributionMetricsSerializer(serializers.Serializer):
    """
    Serializer for topics distribution metrics
    """

    topics = TopicSerializer(many=True)
