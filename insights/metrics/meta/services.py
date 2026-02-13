from datetime import date
from rest_framework.exceptions import ValidationError
from sentry_sdk import capture_exception
import logging

from insights.metrics.meta.aggregations import ConversationsByCategoryAggregations
from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.typing import PricingDataPoint
from insights.metrics.meta.exception import MarketingMessagesStatusError
from insights.metrics.meta.validators import (
    validate_analytics_kwargs,
    validate_list_templates_filters,
)
from django.conf import settings


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

        # [STAGING] Mock list templates
        waba_id = valid_filters.get("waba_id")
        if waba_id in settings.STG_MOCK_META_WABA_IDS:
            return {
                "data": [
                    {
                        "name": "Example",
                        "parameter_format": "POSITIONAL",
                        "components": [
                            {
                                "type": "BODY",
                                "text": "Hello, {{1}}, this is an example",
                            }
                        ],
                        "language": "en_US",
                        "status": "APPROVED",
                        "category": "MARKETING",
                        "id": "123456789098765",
                    }
                ]
            }

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

        # [STAGING] Mock template preview
        waba_id = filters.get("waba_id")
        if waba_id in settings.STG_MOCK_META_WABA_IDS:
            return {
                "is_favorite": False,
                "edit_template_url": None,
                "name": "Example",
                "parameter_format": "POSITIONAL",
                "components": [
                    {
                        "type": "BODY",
                        "text": "Hello, {{1}}, this is an example",
                    },
                    {
                        "type": "BUTTONS",
                        "buttons": [
                            {"type": "QUICK_REPLY", "text": "Ok"},
                            {"type": "QUICK_REPLY", "text": "Cancel"},
                        ],
                    },
                ],
                "language": "en_US",
                "status": "APPROVED",
                "category": "MARKETING",
                "id": "123456789098765",
            }

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

        # [STAGING] Mock messages analytics
        waba_id = filters.get("waba_id")
        if waba_id in settings.STG_MOCK_META_WABA_IDS:
            return {
                "data": {
                    "status_count": {
                        "sent": {"value": 269},
                        "delivered": {"value": 268, "percentage": 99.63},
                        "read": {"value": 203, "percentage": 75.46},
                        "clicked": {"value": 177, "percentage": 65.8},
                    },
                    "data_points": [
                        {
                            "date": "2025-09-26",
                            "sent": 0,
                            "delivered": 0,
                            "read": 0,
                            "clicked": 0,
                        },
                        {
                            "date": "2025-09-27",
                            "sent": 0,
                            "delivered": 0,
                            "read": 0,
                            "clicked": 0,
                        },
                        {
                            "date": "2025-09-28",
                            "sent": 0,
                            "delivered": 0,
                            "read": 0,
                            "clicked": 0,
                        },
                        {
                            "date": "2025-09-29",
                            "sent": 0,
                            "delivered": 0,
                            "read": 0,
                            "clicked": 0,
                        },
                        {
                            "date": "2025-09-30",
                            "sent": 0,
                            "delivered": 0,
                            "read": 0,
                            "clicked": 0,
                        },
                        {
                            "date": "2025-10-01",
                            "sent": 269,
                            "delivered": 268,
                            "read": 201,
                            "clicked": 172,
                        },
                        {
                            "date": "2025-10-02",
                            "sent": 0,
                            "delivered": 0,
                            "read": 2,
                            "clicked": 5,
                        },
                    ],
                }
            }

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

        # [STAGING] Mock buttons analytics
        waba_id = filters.get("waba_id")
        if waba_id in settings.STG_MOCK_META_WABA_IDS:
            return {
                "data": [
                    {
                        "label": "Ok",
                        "type": "QUICK_REPLY",
                        "total": 143,
                        "click_rate": 53.16,
                    },
                    {
                        "label": "Cancel",
                        "type": "QUICK_REPLY",
                        "total": 34,
                        "click_rate": 12.64,
                    },
                ]
            }

        return self.client.get_buttons_analytics(**valid_filters)

    def get_conversations_by_category(
        self, waba_id: int, start_date: date, end_date: date
    ) -> dict:
        """
        Get conversations by category.
        """

        response: dict = self.client.get_conversations_by_category(
            waba_id=waba_id, start_date=start_date, end_date=end_date
        )

        data_points: list[PricingDataPoint] = (
            response.get("pricing_analytics", {})
            .get("data", [{}])[0]
            .get("data_points", [])
        )

        return ConversationsByCategoryAggregations().aggregate_volume_by_category(
            data_points
        )

    def check_marketing_messages_status(self, waba_id: str):
        """
        Check the status of marketing messages.
        """
        try:
            response = self.client.check_marketing_messages_status(waba_id=waba_id)
        except (MarketingMessagesStatusError, Exception) as err:
            logger.error(
                "Error checking marketing messages status: %s. Original exception: %s",
                err.response.text,
                err,
                exc_info=True,
            )
            capture_exception(err)

            return False

        status = response.get("marketing_messages_onboarding_status")
        is_active = status == "ONBOARDED"

        return is_active
