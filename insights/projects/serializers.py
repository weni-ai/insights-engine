from rest_framework import serializers

from insights.projects.models import Project
from insights.projects.services.indexer_activation import is_project_indexer_active


class ProjectSerializer(serializers.ModelSerializer):
    is_indexer_active = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "uuid",
            "name",
            "timezone",
            "is_active",
            "is_indexer_active",
        ]

    def get_is_indexer_active(self, obj: Project) -> bool:
        return is_project_indexer_active(obj)


class ListContactsQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    page_size = serializers.IntegerField(required=False, default=10)
    cursor = serializers.CharField(required=False)


class ListTicketIDsQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    page_size = serializers.IntegerField(required=False, default=10)
    cursor = serializers.CharField(required=False)


class TicketIDSerializer(serializers.Serializer):
    ticket_id = serializers.CharField()
