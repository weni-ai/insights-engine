from rest_framework import serializers

from insights.projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "uuid",
            "name",
            "timezone",
            "is_active",
        ]


class ListContactsQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    page_size = serializers.IntegerField(required=False, default=10)
    cursor = serializers.CharField(required=False)
