from rest_framework import serializers

from insights.projects.models import Project


class UpdateProjectVTEXAccountRequestSerializer(serializers.Serializer):
    vtex_account = serializers.CharField(
        required=True, max_length=100, allow_blank=True, allow_null=True
    )


class ProjectVTEXAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "uuid", "vtex_account"]
