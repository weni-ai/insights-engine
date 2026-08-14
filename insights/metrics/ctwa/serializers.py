from rest_framework import serializers


class CTWADateRangeQueryParamsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date"},
                code="end_date_before_start_date",
            )
        return attrs


class CTWADataQueryParamsSerializer(CTWADateRangeQueryParamsSerializer):
    campaign = serializers.UUIDField(required=False)


class CTWAPerformanceByCampaignQueryParamsSerializer(
    CTWADateRangeQueryParamsSerializer
):
    limit = serializers.IntegerField(
        required=False, default=10, min_value=1, max_value=100
    )
    offset = serializers.IntegerField(required=False, default=0, min_value=0)


class CTWAAttributedRevenueSerializer(serializers.Serializer):
    currency = serializers.CharField()
    value = serializers.FloatField()
    avg = serializers.FloatField()


class CTWADataSerializer(serializers.Serializer):
    attributed_revenue = CTWAAttributedRevenueSerializer()
    ctwa_conversations = serializers.IntegerField()
    organic_conversations = serializers.IntegerField()


class CTWAFunnelStepSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    percentage = serializers.FloatField()


class CTWAConversionsSerializer(serializers.Serializer):
    conversations_started = CTWAFunnelStepSerializer()
    conversations_qualified = CTWAFunnelStepSerializer()
    conversations_converted = CTWAFunnelStepSerializer()


class CTWACampaignPerformanceSerializer(serializers.Serializer):
    campaign = serializers.CharField()
    conversations = serializers.IntegerField()
    qualified = serializers.IntegerField()
    conversions = serializers.IntegerField()
    revenue = serializers.FloatField()
