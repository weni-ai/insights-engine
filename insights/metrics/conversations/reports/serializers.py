from rest_framework import serializers


from insights.reports.choices import ReportFormat
from insights.metrics.conversations.reports.choices import ConversationsReportSections


class ConversationsReportQueryParamsSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(required=True, choices=ReportFormat.choices)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    sections = serializers.ListField(
        required=True,
        child=serializers.ChoiceField(choices=ConversationsReportSections.choices),
    )
