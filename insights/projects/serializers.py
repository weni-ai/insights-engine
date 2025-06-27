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
