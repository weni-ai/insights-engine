from rest_framework import serializers

from .models import Widget


class WidgetSerializer(serializers.ModelSerializer):
    is_configurable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Widget
        fields = "__all__"
