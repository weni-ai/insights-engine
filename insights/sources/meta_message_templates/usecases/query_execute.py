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
                # TODO: Raise error
                pass

            return client.get_template_preview(template_id=template_id)
