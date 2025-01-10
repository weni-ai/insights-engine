from rest_framework.exceptions import ValidationError

from insights.sources.meta_message_templates.clients import MetaAPIClient
from insights.sources.meta_message_templates.enums import Operations
from insights.utils import convert_date_str_to_datetime_date


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

        if operation == Operations.TEMPLATE_PREVIEW.value:
            if not (template_id := filters.get("template_id")):
                raise ValidationError(
                    "Template id is required", code="template_id_missing"
                )

            return client.get_template_preview(template_id=template_id)

        if operation == Operations.MESSAGES_ANALYTICS.value:
            analytics_kwargs = {
                k: None
                for k in ["waba_id", "project", "template_id", "start_date", "end_date"]
            }
            missing_fields = []

            for field in analytics_kwargs.keys():
                if field not in filters:
                    missing_fields.append(field)

                analytics_kwargs[field] = filters.get(field)

            if missing_fields:
                raise ValidationError(
                    {
                        "error": f"Required fields are missing: {', '.join(missing_fields)}"
                    },
                    code="required_fields_missing",
                )

            for dt_field in ["start_date", "end_date"]:
                try:
                    analytics_kwargs[dt_field] = convert_date_str_to_datetime_date(
                        analytics_kwargs[dt_field]
                    )
                except ValueError as err:
                    raise ValidationError(
                        {
                            dt_field: "Invalid date format. Please provide the date in 'YYYY-MM-DD' format, e.g., '2025-12-25'."
                        },
                        code="invalid_date_format",
                    ) from err

            return client.get_messages_analytics(**analytics_kwargs)

        raise ValidationError("Unsupported operation", code="unsupported_operation")
