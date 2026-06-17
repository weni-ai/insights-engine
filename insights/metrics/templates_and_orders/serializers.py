from rest_framework import serializers


class TemplatesAndOrdersQueryParamsSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    utm_source = serializers.CharField(required=True)
    template_name_prefix = serializers.CharField(required=True)
