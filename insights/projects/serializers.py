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
