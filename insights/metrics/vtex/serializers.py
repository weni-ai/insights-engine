from rest_framework import serializers

from insights.metrics.vtex.enums import OrdersSumGranularity, WeekStartsOn


class UTMSourceMetricsQueryParamsSerializer(serializers.Serializer):
    utm_source = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    project_uuid = serializers.UUIDField(required=True)


class InternalVTEXOrdersRequestSerializer(serializers.Serializer):
    utm_source = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    project_uuid = serializers.UUIDField(required=True)


class InternalVTEXOrdersSumRequestSerializer(serializers.Serializer):
    end_date = serializers.DateField(required=True)
    granularity = serializers.ChoiceField(
        choices=OrdersSumGranularity.choices, required=True
    )
    project_uuid = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    utm_source = serializers.CharField(required=True)
    week_starts_on = serializers.ChoiceField(
        choices=WeekStartsOn.choices,
        required=False,
        default=WeekStartsOn.SUNDAY,
    )
