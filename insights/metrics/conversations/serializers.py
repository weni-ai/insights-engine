import pytz
from datetime import datetime, time
from rest_framework import serializers


from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    CsatMetricsType,
    NPSType,
    NpsMetricsType,
)
from insights.metrics.conversations.enums import ConversationType
from insights.projects.models import Project
from insights.widgets.models import Widget


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


class ConversationsTimeseriesDataSerializer(serializers.Serializer):
    """
    Serializer for the conversations timeseries data.
    """

    label = serializers.CharField()
    value = serializers.IntegerField()


class ConversationsTimeseriesMetricsSerializer(serializers.Serializer):
    """
    Serializer for the conversations timeseries metrics.
    """

    unit = serializers.ChoiceField(choices=ConversationsTimeseriesUnit.choices)
    total = ConversationsTimeseriesDataSerializer(many=True)
    by_human = ConversationsTimeseriesDataSerializer(many=True)


class ConversationsTimeseriesMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for the conversations timeseries metrics query params.
    """

    unit = serializers.ChoiceField(choices=ConversationsTimeseriesUnit.choices)


class SubjectMetricDataSerializer(serializers.Serializer):
    """
    Serializer for subject metric data
    """

    name = serializers.CharField()
    percentage = serializers.FloatField()


class SubjectsMetricsSerializer(serializers.Serializer):
    """
    Serializer for subjects metrics
    """

    has_more = serializers.BooleanField()
    subjects = SubjectMetricDataSerializer(many=True)


class ConversationsSubjectsMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for conversations subjects metrics query params
    """

    type = serializers.ChoiceField(
        choices=ConversationsSubjectsType.choices,
    )
    limit = serializers.IntegerField(required=False)


class RoomsByQueueMetricQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for rooms by queue metric query params
    """

    limit = serializers.IntegerField(required=False)


class QueueMetricSerializer(serializers.Serializer):
    """
    Serializer for queue metric
    """

    name = serializers.CharField()
    percentage = serializers.FloatField()


class RoomsByQueueMetricSerializer(serializers.Serializer):
    """
    Serializer for rooms by queue metric
    """

    queues = QueueMetricSerializer(many=True)
    has_more = serializers.BooleanField()


class CsatMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for csat metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(required=True, choices=CsatMetricsType.choices)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": "Widget not found"}, code="widget_not_found"
            )

        attrs["widget"] = widget
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


class NPSQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for NPS query params
    """

    type = serializers.ChoiceField(choices=NPSType.choices, required=True)


class NPSSerializer(serializers.Serializer):
    """
    Serializer for NPS
    """

    score = serializers.FloatField()
    total_responses = serializers.IntegerField()
    promoters = serializers.IntegerField()
    detractors = serializers.IntegerField()
    passives = serializers.IntegerField()


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


class NpsMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for NPS metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(required=True, choices=NpsMetricsType.choices)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": "Widget not found"}, code="widget_not_found"
            )

        attrs["widget"] = widget
        return attrs


class NpsMetricsSerializer(serializers.Serializer):
    """
    Serializer for NPS metrics
    """

    total_responses = serializers.IntegerField()
    promoters = serializers.IntegerField()
    passives = serializers.IntegerField()
    detractors = serializers.IntegerField()
    score = serializers.IntegerField()
