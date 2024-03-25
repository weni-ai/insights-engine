from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    description = serializers.CharField(required=True)
    is_default = serializers.BooleanField(required=True)
    template = serializers.UUIDField(required=False)
