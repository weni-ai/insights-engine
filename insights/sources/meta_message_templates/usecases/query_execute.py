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
            analytics_kwargs = {
                k: None
                for k in ["waba_id", "project", "template_id", "start_date", "end_date"]
            }
            missing_fields = []

            for field in analytics_kwargs.keys():
                if field not in filters:
                    missing_fields.append(field)

            if missing_fields:
                raise ValidationError(
                    {
                        "error": f"Required fields are missing: {', '.join(missing_fields)}"
                    },
                    code="required_fields_missing",
                )

            # TODO: Validate dates

            return client.get_messages_analytics(**analytics_kwargs)

        raise ValidationError("Unsupported operation", code="unsupported_operation")
