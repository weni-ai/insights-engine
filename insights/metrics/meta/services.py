from rest_framework.exceptions import ValidationError

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.validators import (
    validate_analytics_kwargs,
    validate_list_templates_filters,
)


class MetaMessageTemplatesService:
    """
    Service for managing Meta message templates.
    """

    def __init__(self):
        self.client = MetaGraphAPIClient()

    def get_templates_list(self, filters: dict):
        """
        Get a list of message templates.
        """

        valid_filters = validate_list_templates_filters(filters)

        return self.client.get_templates_list(**valid_filters)

    def get_template_preview(self, filters: dict):
        """
        Get a preview of a message template.
        """

        if not (template_id := filters.get("template_id")):
            raise ValidationError(
                {"error": "'template_id' is required"},
                code="template_id_missing",
            )

        return self.client.get_template_preview(template_id=template_id)

    def get_messages_analytics(self, filters: dict, timezone_name: str | None = None):
        """
        Get analytics data for messages sent using a message template.
        """

        valid_filters = validate_analytics_kwargs(filters, timezone_name=timezone_name)

        return self.client.get_messages_analytics(**valid_filters)

    def get_buttons_analytics(self, filters: dict, timezone_name: str | None = None):
        """
        Get analytics data for buttons in a message template.
        """

        valid_filters = validate_analytics_kwargs(filters, timezone_name=timezone_name)

        return self.client.get_buttons_analytics(**valid_filters)
