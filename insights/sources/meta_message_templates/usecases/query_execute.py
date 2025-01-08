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

        if operation == Operations.PREVIEW_TEMPLATE:
            if not (template_id := filters.get("template_id")):
                raise ValidationError(
                    "Template id is required", code="template_id_missing"
                )

            return client.get_template_preview(template_id=template_id)
