import pytz
from datetime import datetime, time

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from insights.metrics.conversations.dataclass import CrosstabItemData
from insights.metrics.conversations.enums import (
    CsatMetricsType,
    ConversationType,
    NpsMetricsType,
)
from insights.projects.models import Project, ProjectAuth
from insights.widgets.models import Widget


class ConversationBaseQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for conversation base query params
    """

    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    project_uuid = serializers.UUIDField()

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"start_date": "Start date must be before end date"},
                code="start_date_after_end_date",
            )

        project = Project.objects.filter(uuid=attrs["project_uuid"]).first()

        if not project:
            raise serializers.ValidationError(
                {"project_uuid": "Project not found"}, code="project_not_found"
            )

        attrs["project"] = project

        timezone = pytz.timezone(project.timezone) if project.timezone else pytz.UTC

        # Convert start_date to datetime at midnight (00:00:00) in project timezone
        start_datetime = datetime.combine(attrs["start_date"].date(), time.min)
        attrs["start_date"] = timezone.localize(start_datetime)

        # Convert end_date to datetime at 23:59:59 in project timezone
        end_datetime = datetime.combine(attrs["end_date"].date(), time(23, 59, 59))
        attrs["end_date"] = timezone.localize(end_datetime)

        return attrs


class CsatMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for csat metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(required=True, choices=CsatMetricsType.choices)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": "Widget not found"}, code="widget_not_found"
            )

        attrs["widget"] = widget
        return attrs


class TopicsDistributionMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for topics distribution metrics query params
    """

    type = serializers.ChoiceField(
        choices=ConversationType.choices,
        required=True,
    )


class SubtopicSerializer(serializers.Serializer):
    """
    Serializer for subtopic
    """

    uuid = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    percentage = serializers.FloatField()


class TopicSerializer(serializers.Serializer):
    """
    Serializer for topic
    """

    uuid = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    percentage = serializers.FloatField()
    subtopics = SubtopicSerializer(many=True)


class TopicsDistributionMetricsSerializer(serializers.Serializer):
    """
    Serializer for topics distribution metrics
    """

    topics = TopicSerializer(many=True)


class GetTopicsQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for getting conversation topics
    """

    project_uuid = serializers.UUIDField(required=True)


class BaseTopicSerializer(serializers.Serializer):
    """
    Serializer for conversation topic
    """

    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class CreateTopicSerializer(BaseTopicSerializer):
    """
    Serializer for creating a conversation topic
    """

    project_uuid = serializers.UUIDField(required=True)


class DeleteTopicSerializer(serializers.Serializer):
    """
    Serializer for deleting a conversation topic
    """

    project_uuid = serializers.UUIDField(required=True)


class ConversationsTotalsMetricSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics by type
    """

    value = serializers.IntegerField()
    percentage = serializers.FloatField()


class ConversationTotalsMetricsSerializer(serializers.Serializer):
    """
    Serializer for conversation totals metrics
    """

    total_conversations = ConversationsTotalsMetricSerializer()
    resolved = ConversationsTotalsMetricSerializer()
    unresolved = ConversationsTotalsMetricSerializer()
    transferred_to_human = ConversationsTotalsMetricSerializer()


class ConversationTotalsMetricsQueryParamsSerializer(
    ConversationBaseQueryParamsSerializer
):
    """
    Serializer for conversation totals metrics query params
    """


class NpsMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for NPS metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(required=True, choices=NpsMetricsType.choices)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": "Widget not found"}, code="widget_not_found"
            )

        attrs["widget"] = widget
        return attrs


class NpsMetricsSerializer(serializers.Serializer):
    """
    Serializer for NPS metrics
    """

    total_responses = serializers.IntegerField()
    promoters = serializers.FloatField()
    passives = serializers.FloatField()
    detractors = serializers.FloatField()
    score = serializers.FloatField()


class CustomMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for custom metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": "Widget not found"}, code="widget_not_found"
            )

        attrs["widget"] = widget
        return attrs


class SalesFunnelMetricsQueryParamsSerializer(ConversationBaseQueryParamsSerializer):
    """
    Serializer for sales funnel metrics query params
    """

    widget_uuid = serializers.UUIDField(required=True)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"], dashboard__project=attrs["project"]
        ).first()

        if not widget:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget not found")}, code="widget_not_found"
            )

        if widget.source != "conversations.sales_funnel":
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget source is not sales funnel")},
                code="widget_source_not_sales_funnel",
            )

        if widget.type != "sales_funnel":
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget type is not sales funnel")},
                code="widget_type_not_sales_funnel",
            )

        attrs["widget"] = widget
        return attrs


class ValueAndPercentageSerializer(serializers.Serializer):
    full_value = serializers.IntegerField()
    value = serializers.FloatField()


class SalesFunnelMetricsSerializer(serializers.Serializer):
    """
    Serializer for sales funnel metrics
    """

    currency = serializers.CharField(source="currency_code")
    total_orders = serializers.IntegerField(source="total_orders_count")
    total_value = serializers.IntegerField(source="total_orders_value")
    average_ticket = serializers.IntegerField()
    captured_leads = serializers.SerializerMethodField()
    purchases_made = serializers.SerializerMethodField()

    def get_captured_leads(self, obj) -> ValueAndPercentageSerializer:
        return ValueAndPercentageSerializer(
            {"full_value": obj.leads_count, "value": 100.00}
        ).data

    def get_purchases_made(self, obj) -> ValueAndPercentageSerializer:
        full_value = obj.total_orders_count
        value = (
            round((full_value / obj.leads_count) * 100, 2) if obj.leads_count > 0 else 0
        )

        return ValueAndPercentageSerializer(
            {"full_value": full_value, "value": value}
        ).data


class CrosstabQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for crosstab query params
    """

    widget_uuid = serializers.UUIDField(required=True)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)

    def _validate_widget_type_and_source(self, widget: Widget) -> None:
        """
        Validate widget type and source
        """
        if widget.type != "conversation.crosstab":
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget type is not crosstab")},
                code="widget_type_not_crosstab",
            )

        if widget.source != "conversation.crosstab":
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget source is not crosstab")},
                code="widget_source_not_crosstab",
            )

    def _validate_widget_config(self, widget: Widget) -> None:
        """
        Validate widget config
        """
        config = widget.config or {}
        source_a = config.get("source_a")
        source_b = config.get("source_b")

        if not source_a or not source_b:
            raise serializers.ValidationError(
                {
                    "widget_uuid": _(
                        "Widget config is not valid, must have source_a and source_b"
                    )
                },
                code="widget_config_not_valid",
            )

        if not source_a.get("key") or not source_b.get("key"):
            raise serializers.ValidationError(
                {
                    "widget_uuid": _(
                        "Widget config is not valid, must have key for source_a and source_b"
                    )
                },
                code="widget_config_not_valid",
            )

    def _validate_widget(self, attrs: dict) -> dict:
        """
        Validate widget
        """
        request = self.context.get("request")
        user = request.user

        widget = Widget.objects.filter(
            uuid=attrs["widget_uuid"],
            dashboard__project__in=ProjectAuth.objects.filter(
                user=user, role=1
            ).values_list("project", flat=True),
        ).first()

        if widget is None:
            raise serializers.ValidationError(
                {"widget_uuid": _("Widget not found")}, code="widget_not_found"
            )

        self._validate_widget_type_and_source(widget)
        self._validate_widget_config(widget)

        return widget

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)
        attrs["widget"] = self._validate_widget(attrs)

        return attrs


class CrosstabSubItemSerializer(serializers.Serializer):
    """
    Serializer for crosstab sub item
    """

    value = serializers.FloatField(source="percentage")


class CrosstabItemSerializer(serializers.Serializer):
    """
    Serializer for crosstab item
    """

    title = serializers.CharField()
    total = serializers.IntegerField()
    events = serializers.SerializerMethodField()

    def get_events(self, obj: CrosstabItemData) -> dict:
        """
        Get events (subitems)
        """
        return {
            item.title: CrosstabSubItemSerializer(item).data for item in obj.subitems
        }
