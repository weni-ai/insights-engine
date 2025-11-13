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


class SetProjectAsSecondarySerializer(serializers.Serializer):
    """
    Serializer to set a project as secondary.
    """

    main_project = serializers.UUIDField(required=True, allow_null=False)


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
