from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.enums import Operations
from insights.sources.meta_message_templates.validators import (
    validate_analytics_kwargs,
)


class QueryExecutor:
    @staticmethod
    def execute(
        filters: dict,
        operation: str,
        parser: callable = None,
        query_kwargs={},
        *args,
        **kwargs,
    ):
        client = MetaAPIClient()

        match operation:
            case Operations.LIST_TEMPLATES.value:
                if not (waba_id := filters.get("waba_id")):
                    raise ValidationError("WABA id is required", code="waba_id_missing")

                return client.get_templates_list(waba_id=waba_id)

            case Operations.TEMPLATE_PREVIEW.value:
                if not (template_id := filters.get("template_id")):
                    raise ValidationError(
                        {"error": "'template_id' is required"},
                        code="template_id_missing",
                    )

                return client.get_template_preview(template_id=template_id)

            case Operations.MESSAGES_ANALYTICS.value:
                analytics_kwargs = validate_analytics_kwargs(filters)

                return client.get_messages_analytics(**analytics_kwargs)

            case Operations.BUTTONS_ANALYTICS.value:
                analytics_kwargs = validate_analytics_kwargs(filters)

                return client.get_buttons_analytics(**analytics_kwargs)

        raise ValidationError("Unsupported operation", code="unsupported_operation")
