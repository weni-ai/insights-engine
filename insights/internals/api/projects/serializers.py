from rest_framework import serializers

from insights.projects.models import Project


class UpdateProjectVTEXAccountRequestSerializer(serializers.Serializer):
    vtex_account = serializers.CharField(
        required=True, max_length=100, allow_blank=True, allow_null=True
    )


class UnlinkedProjectSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    name = serializers.CharField()


class ProjectVTEXAccountSerializer(serializers.ModelSerializer):
    projects_unlinked = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["name", "uuid", "vtex_account", "projects_unlinked"]

    def get_projects_unlinked(self, obj):
        projects = self.context.get("projects_unlinked", [])
        return UnlinkedProjectSerializer(projects, many=True).data
