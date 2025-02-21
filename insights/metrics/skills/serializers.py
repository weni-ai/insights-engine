from rest_framework import serializers


class SkillMetricsQueryParamsSerializer(serializers.Serializer):
    skill = serializers.CharField(required=True)
    project_uuid = serializers.UUIDField(required=True)
