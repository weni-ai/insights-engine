from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.enums import Operations


class QueryExecutor:
    @staticmethod
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs={},
        *args,
        **kwargs,
    ):
        client = MetaAPIClient()

        if operation == Operations.MESSAGES_ANALYTICS.value:
            required_fields = ["template_id", "start_date", "end_date"]
            missing_fields = []

            analytics_params = {}

            for field in required_fields:
                if field not in filters:
                    missing_fields.append(field)

                analytics_params[field] = filters.get(field)

            if missing_fields:
                raise ValidationError(
                    {
                        "error": f"Required fields are missing: {', '.join(missing_fields)}"
                    },
                    code="required_fields_missing",
                )

            # TODO: Validate dates

            # TODO: Get business id related to the template
            analytics_params["business_id"] = "TODO"

            return client.get_messages_analytics(**analytics_params)

        raise ValidationError("Unsupported operation", code="unsupported_operation")
