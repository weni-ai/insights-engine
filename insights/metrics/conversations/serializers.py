import pytz
from datetime import datetime, time
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

        timezone = pytz.timezone(project.timezone) if project.timezone else pytz.UTC

        # Convert start_date to datetime at midnight (00:00:00) in project timezone
        start_datetime = datetime.combine(attrs["start_date"], time.min)
        attrs["start_date"] = timezone.localize(start_datetime)

        # Convert end_date to datetime at 23:59:59 in project timezone
        end_datetime = datetime.combine(attrs["end_date"], time(23, 59, 59))
        attrs["end_date"] = timezone.localize(end_datetime)

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

    uuid = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    percentage = serializers.FloatField()


class TopicSerializer(serializers.Serializer):
    """
    Serializer for topic
    """

    uuid = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    percentage = serializers.FloatField()
    subtopics = SubtopicSerializer(many=True)


class TopicsDistributionMetricsSerializer(serializers.Serializer):
    """
    Serializer for topics distribution metrics
    """

    topics = TopicSerializer(many=True)


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


class ConversationsTotalsMetricSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics by type
    """

    value = serializers.IntegerField()
    percentage = serializers.FloatField()


class ConversationTotalsMetricsSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics
    """

    total_conversations = ConversationsTotalsMetricSerializer()
    resolved = ConversationsTotalsMetricSerializer()
    unresolved = ConversationsTotalsMetricSerializer()
    abandoned = ConversationsTotalsMetricSerializer()
    transferred_to_human = ConversationsTotalsMetricSerializer()


class ConversationTotalsMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for conversation totals metrics query params
    """
