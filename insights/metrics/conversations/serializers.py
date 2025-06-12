from rest_framework import serializers


from insights.metrics.conversations.enums import ConversationsTimeseriesUnit


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
