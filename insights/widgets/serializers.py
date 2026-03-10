from typing import Optional
from rest_framework import serializers

from .models import Widget


class WidgetSerializer(serializers.ModelSerializer):
    is_configurable = serializers.BooleanField(read_only=True)
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Widget
        fields = "__all__"

    def get_parent(self, obj: Widget) -> Optional[dict]:
        if not obj.parent:
            return None

        return {"uuid": obj.parent.uuid, "dashboard": obj.parent.dashboard_id}
