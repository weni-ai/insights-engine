from rest_framework import serializers

from insights.metrics.meta.validators import validate_analytics_selected_period


class OrdersConversionsUTMDataSerializer(serializers.Serializer):
    count_sell = serializers.IntegerField(required=True)
    accumulated_total = serializers.FloatField(required=True)
    medium_ticket = serializers.FloatField(required=True)
    currency_code = serializers.CharField(required=True)


class OrdersConversionsFiltersSerializer(serializers.Serializer):
    utm_source = serializers.CharField(required=True)
    waba_id = serializers.CharField(required=True)
    template_id = serializers.CharField(required=True)

    # This is a workaround to maintain the same filter names
    # and format as the dashboard, sent by default by the frontend application.
    ended_at__gte = serializers.DateTimeField(required=True, write_only=True)
    ended_at__lte = serializers.DateTimeField(required=True, write_only=True)

    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        start_date = attrs.get("ended_at__gte")
        end_date = attrs.get("ended_at__lte")

        if start_date > end_date:
            raise serializers.ValidationError(
                {"ended_at__lte": "End date must be after start date"},
                code="end_date_before_start_date",
            )

        validate_analytics_selected_period(
            start_date.date(), field_name="ended_at__gte"
        )

        attrs["start_date"] = start_date
        attrs["end_date"] = end_date

        return attrs


class OrdersConversionsGraphDataFieldSerializer(serializers.Serializer):
    value = serializers.IntegerField(required=True)
    percentage = serializers.FloatField(required=True)


class OrdersConversionsGraphDataSerializer(serializers.Serializer):
    sent = OrdersConversionsGraphDataFieldSerializer(required=True)
    delivered = OrdersConversionsGraphDataFieldSerializer(required=True)
    read = OrdersConversionsGraphDataFieldSerializer(required=True)
    clicked = OrdersConversionsGraphDataFieldSerializer(required=True)
    orders = OrdersConversionsGraphDataFieldSerializer(required=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # All percentages are related to the sent value, so we don't need to show it
        # for the sent field itself.
        del data["sent"]["percentage"]

        return data


class OrdersConversionsMetricsSerializer(serializers.Serializer):
    utm_data = OrdersConversionsUTMDataSerializer(required=True)
    graph_data = OrdersConversionsGraphDataSerializer(required=True)
