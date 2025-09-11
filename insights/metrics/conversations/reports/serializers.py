from rest_framework import serializers

from django.utils.translation import gettext_lazy as _

from insights.reports.choices import ReportFormat
from insights.reports.models import Report
from insights.metrics.conversations.reports.choices import ConversationsReportSections
from insights.projects.models import Project
from insights.widgets.models import Widget


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

    def validate(self, attrs: dict) -> dict:
        """
        Validate query params
        """
        attrs = super().validate(attrs)

        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError(
                {"start_date": [_("Start date must be before end date")]},
                code="start_date_after_end_date",
            )

        if ("sections" not in attrs or not attrs["sections"]) and (
            "custom_widgets" not in attrs or not attrs["custom_widgets"]
        ):
            raise serializers.ValidationError(
                {
                    "sections": [_("Sections or custom widgets are required")],
                    "custom_widgets": [_("Sections or custom widgets are required")],
                },
                code="sections_or_custom_widgets_required",
            )

        project_widgets = Widget.objects.filter(
            dashboard__project=attrs["project"]
        ).values_list("uuid", flat=True)

        if "custom_widgets" in attrs and attrs["custom_widgets"]:
            not_found_widgets = set(attrs["custom_widgets"]) - set(project_widgets)

            if not_found_widgets:
                raise serializers.ValidationError(
                    {
                        "custom_widgets": [
                            _("Widget {widget_uuid} not found").format(
                                widget_uuid=widget_uuid
                            )
                            for widget_uuid in not_found_widgets
                        ]
                    },
                    code="widgets_not_found",
                )

        return attrs


class GetConversationsReportStatusResponseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="requested_by.email", allow_null=True)
    report_uuid = serializers.UUIDField(source="uuid")

    class Meta:
        model = Report
        fields = ["email", "report_uuid", "status"]
