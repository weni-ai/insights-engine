from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Widget


class WidgetSerializer(serializers.ModelSerializer):
    is_configurable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Widget
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        super().validate(attrs)
        instance: Widget = self.instance

        if instance is not None:
            widget = Widget.objects.get(pk=instance.pk)
            for key, value in attrs.items():
                setattr(widget, key, value)
        else:
            widget = Widget(**attrs)

        try:
            widget.full_clean()
        except DjangoValidationError as e:
            if hasattr(e, "message_dict") and e.message_dict:
                messages = e.message_dict.get(
                    "__all__", list(e.message_dict.values())[0]
                )
                message = messages[0] if messages else str(e)
            else:
                message = e.messages[0] if e.messages else str(e)
            raise serializers.ValidationError(
                {"error": message},
                code=getattr(e, "code", None),
            )

        return attrs
