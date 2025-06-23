from rest_framework import serializers


from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
    NPSType,
)
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


class ConversationTotalsMetricsByTypeSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics by type
    """

    value = serializers.IntegerField()
    percentage = serializers.FloatField()


class ConversationTotalsMetricsSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics
    """

    total = serializers.IntegerField()
    by_ai = ConversationTotalsMetricsByTypeSerializer()
    by_human = ConversationTotalsMetricsByTypeSerializer()


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


class SubjectsDistributionMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for subjects distribution metrics query params
    """


class SubjectItemSerializer(serializers.Serializer):
    """
    Serializer for subject item
    """

    name = serializers.CharField()
    percentage = serializers.FloatField()


class SubjectGroupSerializer(serializers.Serializer):
    """
    Serializer for subject group
    """

    name = serializers.CharField()
    percentage = serializers.FloatField()
    subjects = SubjectItemSerializer(many=True)


class SubjectsDistributionMetricsSerializer(serializers.Serializer):
    """
    Serializer for subjects distribution metrics
    """

    groups = SubjectGroupSerializer(many=True)


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
