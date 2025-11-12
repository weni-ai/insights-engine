from datetime import datetime, time
import pytz


from rest_framework import serializers

from django.utils.translation import gettext_lazy as _

from insights.metrics.conversations.reports.available_widgets import (
    get_csat_ai_widget,
    get_csat_human_widget,
    get_custom_widgets,
    get_nps_ai_widget,
    get_nps_human_widget,
)
from insights.reports.choices import ReportFormat
from insights.reports.models import Report
from insights.metrics.conversations.reports.choices import ConversationsReportSections
from insights.projects.models import Project
from insights.dashboards.models import CONVERSATIONS_DASHBOARD_NAME, Dashboard


class BaseConversationsReportParamsSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        project = Project.objects.filter(uuid=attrs["project_uuid"]).first()

        if not project:
            raise serializers.ValidationError(
                {"project_uuid": [_("Project not found")]}, code="project_not_found"
            )

        attrs["project"] = project

        return attrs


class GetConversationsReportStatusQueryParamsSerializer(
    BaseConversationsReportParamsSerializer
):
    pass


class RequestConversationsReportGenerationSerializer(
    BaseConversationsReportParamsSerializer
):
    type = serializers.ChoiceField(required=True, choices=ReportFormat.choices)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    sections = serializers.ListField(
        required=False,
        child=serializers.ChoiceField(choices=ConversationsReportSections.choices),
    )
    custom_widgets = serializers.ListField(
        required=False,
        child=serializers.UUIDField(),
    )
    start = serializers.DateTimeField(read_only=True)
    end = serializers.DateTimeField(read_only=True)

    def _validate_dates(self, attrs: dict) -> dict:
        """
        Validate dates
        """
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"error": _("Start date must be before end date")},
                code="start_date_after_end_date",
            )

    def _validate_sections_and_custom_widgets(self, attrs: dict) -> dict:
        """
        Validate sections and custom widgets
        """
        if ("sections" not in attrs or not attrs["sections"]) and (
            "custom_widgets" not in attrs or not attrs["custom_widgets"]
        ):
            raise serializers.ValidationError(
                {"error": _("Sections or custom widgets are required")},
                code="sections_or_custom_widgets_required",
            )

        project_custom_widgets_uuids = get_custom_widgets(attrs["project"])

        if "custom_widgets" in attrs and attrs["custom_widgets"]:
            not_found_widgets = set(attrs["custom_widgets"]) - set(
                project_custom_widgets_uuids
            )

            if not_found_widgets:
                raise serializers.ValidationError(
                    {
                        "error": ",".join(
                            [
                                _("Widget %(widget_uuid)s not found")
                                % {"widget_uuid": widget_uuid}
                                for widget_uuid in not_found_widgets
                            ]
                        ),
                    },
                    code="widgets_not_found",
                )

    def _validate_sections(self, attrs: dict) -> dict:
        sections = attrs.get("sections", [])
        attrs["source_config"] = {}

        dashboards_uuids = Dashboard.objects.filter(
            project=attrs["project"], name=CONVERSATIONS_DASHBOARD_NAME
        ).values_list("uuid", flat=True)

        if not dashboards_uuids:
            raise serializers.ValidationError(
                {"error": _("Conversations dashboard not found")},
                code="conversations_dashboard_not_found",
            )

        if sections:
            if "CSAT_AI" in sections:
                widget = get_csat_ai_widget(attrs["project"])

                if not widget:
                    raise serializers.ValidationError(
                        {
                            "error": _(
                                "CSAT AI widget not found or not configured correctly"
                            )
                        },
                        code="csat_ai_widget_not_found",
                    )

                agent_uuid = widget.config.get("datalake_config", {}).get("agent_uuid")

                if not agent_uuid:
                    raise serializers.ValidationError(
                        {"error": _("Agent UUID not found in widget config")},
                        code="agent_uuid_not_found_in_widget_config",
                    )

                attrs["source_config"]["csat_ai_agent_uuid"] = agent_uuid

            if "NPS_AI" in sections:
                widget = get_nps_ai_widget(attrs["project"])

                if not widget:
                    raise serializers.ValidationError(
                        {
                            "error": _(
                                "NPS AI widget not found or not configured correctly"
                            )
                        },
                        code="nps_ai_widget_not_found",
                    )

                agent_uuid = widget.config.get("datalake_config", {}).get("agent_uuid")

                if not agent_uuid:
                    raise serializers.ValidationError(
                        {"error": _("Agent UUID not found in widget config")},
                        code="agent_uuid_not_found_in_widget_config",
                    )

                attrs["source_config"]["nps_ai_agent_uuid"] = agent_uuid

            if "CSAT_HUMAN" in sections:
                widget = get_csat_human_widget(attrs["project"])

                if not widget:
                    raise serializers.ValidationError(
                        {
                            "error": _(
                                "CSAT human widget not found or not configured correctly"
                            )
                        },
                        code="csat_human_widget_not_found",
                    )

                csat_human_flow_uuid = widget.config.get("filter", {}).get("flow")
                csat_human_op_field = widget.config.get("op_field", None)

                if not csat_human_flow_uuid:
                    raise serializers.ValidationError(
                        {"error": _("Flow UUID not found in widget config")},
                        code="flow_uuid_not_found_in_widget_config",
                    )

                if not csat_human_op_field:
                    raise serializers.ValidationError(
                        {"error": _("Op field not found in widget config")},
                        code="op_field_not_found_in_widget_config",
                    )

                attrs["source_config"]["csat_human_flow_uuid"] = csat_human_flow_uuid
                attrs["source_config"]["csat_human_op_field"] = csat_human_op_field

            if "NPS_HUMAN" in sections:
                widget = get_nps_human_widget(attrs["project"])

                if not widget:
                    raise serializers.ValidationError(
                        {
                            "error": _(
                                "NPS human widget not found or not configured correctly"
                            )
                        },
                        code="nps_human_widget_not_found",
                    )

                nps_human_flow_uuid = widget.config.get("filter", {}).get("flow")
                nps_human_op_field = widget.config.get("op_field", None)

                if not nps_human_flow_uuid:
                    raise serializers.ValidationError(
                        {"error": _("Flow UUID not found in widget config")},
                        code="flow_uuid_not_found_in_widget_config",
                    )

                if not nps_human_op_field:
                    raise serializers.ValidationError(
                        {"error": _("Op field not found in widget config")},
                        code="op_field_not_found_in_widget_config",
                    )

                attrs["source_config"]["nps_human_flow_uuid"] = nps_human_flow_uuid
                attrs["source_config"]["nps_human_op_field"] = nps_human_op_field

        return attrs

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        self._validate_dates(attrs)
        self._validate_sections_and_custom_widgets(attrs)
        attrs = self._validate_sections(attrs)

        timezone = (
            pytz.timezone(attrs["project"].timezone)
            if attrs["project"].timezone
            else pytz.UTC
        )

        start_datetime = datetime.combine(attrs["start_date"], time.min)
        attrs["start"] = timezone.localize(start_datetime)

        end_datetime = datetime.combine(attrs["end_date"], time(23, 59, 59))
        attrs["end"] = timezone.localize(end_datetime)
        attrs.pop("start_date")
        attrs.pop("end_date")

        return attrs


class GetConversationsReportStatusResponseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="requested_by.email", allow_null=True)
    report_uuid = serializers.UUIDField(source="uuid")

    class Meta:
        model = Report
        fields = ["email", "report_uuid", "status"]


class AvailableReportWidgetsQueryParamsSerializer(
    BaseConversationsReportParamsSerializer
):
    pass


class AvailableReportWidgetsResponseSerializer(serializers.Serializer):
    sections = serializers.ListField(child=serializers.CharField())
    custom_widgets = serializers.ListField(child=serializers.UUIDField())
