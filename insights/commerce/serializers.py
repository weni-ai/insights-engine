from rest_framework import serializers


class AbandonedCartStatusResponseSerializer(serializers.Serializer):
    active = serializers.BooleanField()


class MarketingPricingResponseSerializer(serializers.Serializer):
    value = serializers.FloatField()
    currency = serializers.CharField()
