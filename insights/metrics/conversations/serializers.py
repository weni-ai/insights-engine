from rest_framework import serializers


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
