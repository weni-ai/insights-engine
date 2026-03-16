from uuid import UUID

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from insights.metrics.conversations.enums import AbsoluteNumbersMetricsType
from insights.widgets.models import Widget


class GetAbsoluteNumbersWidgetUseCase:
    """
    Use case to validate and retrieve an absolute numbers child widget.
    """

    def execute(self, widget_uuid: UUID) -> Widget:
        widget = Widget.objects.filter(uuid=widget_uuid).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget not found")}, code="widget_not_found"
            )

        config = widget.config or {}
        source = widget.source
        operation = config.get("operation")
        key = config.get("key")
        agent_uuid = config.get("datalake_config", {}).get("agent_uuid")

        if source != "conversations.absolute_numbers.child":
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget source is not absolute numbers child")},
                code="widget_source_not_absolute_numbers_child",
            )

        if operation not in AbsoluteNumbersMetricsType.values:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget operation is not valid")},
                code="widget_operation_not_valid",
            )

        if not key:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget key is not valid")},
                code="widget_key_not_valid",
            )

        if not agent_uuid:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget agent UUID is not valid")},
                code="widget_agent_uuid_not_valid",
            )

        return widget
