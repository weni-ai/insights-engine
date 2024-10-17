from insights.sources.chat_completion.clients import ChatCompletionClient


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        return_format: str = None,
        project: object = None,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        client = ChatCompletionClient()
        query_results = client.chat_completion(filters)

        gpt_answer = (
            query_results.get("choices", [{}])[0].get("message", {}).get("content", "")
        )

        return {
            "value": gpt_answer,
        }
