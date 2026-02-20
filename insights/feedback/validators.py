from abc import ABC

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from insights.feedback.choices import DashboardTypes
from insights.feedback.serializers.conversational import (
    ConversationalFeedbackSerializer,
)


SERIALIZER_MAPPING = {
    DashboardTypes.CONVERSATIONAL: ConversationalFeedbackSerializer,
}


class BaseFeedbackDataValidator(ABC):
    def parse_data(self, data: dict) -> dict:
        raise NotImplementedError("Subclasses must implement this method")

    def validate(self, dashboard_type: DashboardTypes, data: dict):
        raise NotImplementedError("Subclasses must implement this method")


class FeedbackDataValidator(BaseFeedbackDataValidator):
    def parse_data(self, data: dict) -> dict:
        answers = data.get("answers", [])

        parsed_data = {}

        for answer in answers:
            if not "reference" in answer:
                raise serializers.ValidationError(
                    _("Reference is required"), code="required"
                )

            reference = answer.pop("reference")

            if reference in parsed_data:
                raise serializers.ValidationError(
                    _("Reference must be unique"), code="unique"
                )

            parsed_data[reference] = answer

        return parsed_data

    def validate(self, dashboard_type: DashboardTypes, data: dict):
        serializer_class = SERIALIZER_MAPPING.get(dashboard_type)

        if not serializer_class:
            raise serializers.ValidationError(
                _("Invalid dashboard type: {dashboard_type}").format(
                    dashboard_type=dashboard_type
                ),
                code="invalid_dashboard_type",
            )

        parsed_data = self.parse_data(data)
        serializer = serializer_class(data=parsed_data)

        serializer.is_valid(raise_exception=True)

        return serializer.validated_data
