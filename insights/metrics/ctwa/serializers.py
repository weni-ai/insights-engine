from rest_framework import serializers


class CTWADataQueryParamsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    campaign = serializers.UUIDField(required=False)

    def validate(self, attrs: dict) -> dict:
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date"},
                code="end_date_before_start_date",
            )
        return attrs


class CTWAAttributedRevenueSerializer(serializers.Serializer):
    currency = serializers.CharField()
    value = serializers.FloatField()
    avg = serializers.FloatField()


class CTWADataSerializer(serializers.Serializer):
    attributed_revenue = CTWAAttributedRevenueSerializer()
    ctwa_conversations = serializers.IntegerField()
    organic_conversations = serializers.IntegerField()
