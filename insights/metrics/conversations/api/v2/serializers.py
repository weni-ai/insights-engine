from rest_framework import serializers

from insights.metrics.conversations.api.v1.serializers import (
    NpsMetricsQueryParamsSerializer,
)


class NpsMetricsQueryParamsSerializerV2(NpsMetricsQueryParamsSerializer):
    """
    Serializer for NPS metrics query params
    """


class NpsMetricsFieldSerializer(serializers.Serializer):
    """
    Serializer for NPS metrics field
    """

    # Percentage
    value = serializers.FloatField(source="percentage")

    # Original value
    full_value = serializers.IntegerField(source="count")


class NpsMetricsSerializerV2(serializers.Serializer):
    """
    Serializer for NPS metrics
    """

    total_responses = serializers.IntegerField()
    promoters = NpsMetricsFieldSerializer()
    passives = NpsMetricsFieldSerializer()
    detractors = NpsMetricsFieldSerializer()
    score = serializers.FloatField()
