from insights.sources.template_messages.clients import (
    TemplateMessagesAuthDetailsRESTClient,
)


class QueryExecutor:
    def execute(
        filters: dict,
        operation: dict,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs,
    ):
        client = TemplateMessagesAuthDetailsRESTClient(
            template_id=filters.get("template_id")
        )

        return client.get_template_message_auth_details()
