from rest_framework import serializers

from insights.metrics.meta.validators import validate_analytics_selected_period


class OrdersConversionsFiltersSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=True)
    template_id = serializers.CharField(required=True)

    # This is a workaround to maintain the same filter names as the dashboard,
    # sent by default by the frontend application.
    ended_at__gte = serializers.DateField(required=True, write_only=True)
    ended_at__lte = serializers.DateField(required=True, write_only=True)

    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)

    def validate(self, attrs):
        ended_at__gte = attrs.get("ended_at__gte")
        ended_at__lte = attrs.get("ended_at__lte")

        if ended_at__gte > ended_at__lte:
            raise serializers.ValidationError(
                {"ended_at__lte": "End date must be after start date"},
                code="end_date_before_start_date",
            )

        validate_analytics_selected_period(ended_at__gte, field_name="ended_at__gte")

        attrs["start_date"] = ended_at__gte
        attrs["end_date"] = ended_at__lte

        return attrs


class OrdersConversionsGraphDataFieldSerializer(serializers.Serializer):
    value = serializers.IntegerField(required=True)
    percentage = serializers.FloatField(required=True)


class OrdersConversionsGraphDataSerializer(serializers.Serializer):
    sent = OrdersConversionsGraphDataFieldSerializer(required=True)
    delivered = OrdersConversionsGraphDataFieldSerializer(required=True)
    read = OrdersConversionsGraphDataFieldSerializer(required=True)
    clicked = OrdersConversionsGraphDataFieldSerializer(required=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # All percentages are related to the sent value, so we don't need to show it
        # for the sent field itself.
        del data["sent"]["percentage"]

        return data


class OrdersConversionsMetricsSerializer(serializers.Serializer):
    graph_data = OrdersConversionsGraphDataSerializer(required=True)
