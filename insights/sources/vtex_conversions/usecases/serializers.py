from rest_framework import serializers

from insights.metrics.meta.validators import validate_analytics_selected_period


class OrdersConversionsFiltersSerializer(serializers.Serializer):
    waba_id = serializers.CharField(required=True)
    template_id = serializers.CharField(required=True)
    date_start = serializers.DateField(required=True)
    date_end = serializers.DateField(required=True)

    def validate(self, attrs):
        date_start = attrs.get("date_start")
        date_end = attrs.get("date_end")

        if date_start > date_end:
            raise serializers.ValidationError(
                {"date_end": "End date must be after start date"},
                code="end_date_before_start_date",
            )

        validate_analytics_selected_period(date_start, field_name="date_start")

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
