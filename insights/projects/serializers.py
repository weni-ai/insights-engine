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


class ListTicketIDsQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    page_size = serializers.IntegerField(required=False, default=10)
    cursor = serializers.CharField(required=False)


class TicketIDSerializer(serializers.Serializer):
    ticket_id = serializers.CharField()


class MetaCampaignQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    limit = serializers.IntegerField(
        required=False, default=10, min_value=1, max_value=100
    )
    offset = serializers.IntegerField(required=False, default=0, min_value=0)


class MetaCampaignSerializer(serializers.Serializer):
    name = serializers.CharField()
    uuid = serializers.CharField()


class ListChannelsQueryParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    limit = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=100
    )
    offset = serializers.IntegerField(required=False, default=0, min_value=0)


class ChannelSerializer(serializers.Serializer):
    name = serializers.CharField()
    uuid = serializers.CharField()
