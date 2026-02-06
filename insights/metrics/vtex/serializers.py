from rest_framework import serializers


class InternalVTEXOrdersRequestSerializer(serializers.Serializer):
    utm_source = serializers.CharField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    project_uuid = serializers.UUIDField(required=True)
