from rest_framework import serializers


class CheckSurveyQueryParamsSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    dashboard = serializers.UUIDField(required=True)


class CheckSurveyResponseSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)
    user_answered = serializers.BooleanField(required=True)
    uuid = serializers.UUIDField(required=False, allow_null=True)
