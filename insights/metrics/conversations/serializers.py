from rest_framework import serializers


from insights.metrics.conversations.enums import ConversationsTimeseriesUnit
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
