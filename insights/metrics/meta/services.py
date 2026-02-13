from rest_framework.exceptions import ValidationError
from sentry_sdk import capture_exception
import logging

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.exception import MarketingMessagesStatusError
from insights.metrics.meta.validators import (
    validate_analytics_kwargs,
    validate_list_templates_filters,
)


logger = logging.getLogger(__name__)


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

    def get_messages_analytics(
        self,
        filters: dict,
        timezone_name: str | None = None,
        skip_kwargs_validation: bool = False,
        include_data_points: bool = True,
        return_exceptions: bool = False,
    ):
        """
        Get analytics data for messages sent using a message template.
        """

        if not skip_kwargs_validation:
            valid_filters = validate_analytics_kwargs(
                filters, timezone_name=timezone_name
            )
        else:
            valid_filters = filters

        return self.client.get_messages_analytics(
            **valid_filters,
            include_data_points=include_data_points,
            return_exceptions=return_exceptions,
        )

    def get_buttons_analytics(self, filters: dict, timezone_name: str | None = None):
        """
        Get analytics data for buttons in a message template.
        """

        valid_filters = validate_analytics_kwargs(filters, timezone_name=timezone_name)

        return self.client.get_buttons_analytics(**valid_filters)

    def check_marketing_messages_status(self, waba_id: str):
        """
        Check the status of marketing messages.
        """
        try:
            response = self.client.check_marketing_messages_status(waba_id=waba_id)
        except (MarketingMessagesStatusError, Exception) as err:
            logger.error(
                "Error checking marketing messages status: %s", err, exc_info=True
            )
            capture_exception(err)

            return False

        status = response.get("marketing_messages_onboarding_status")
        is_active = status == "ONBOARDED"

        return is_active
