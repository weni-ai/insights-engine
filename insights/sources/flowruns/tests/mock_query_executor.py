class MockFlowRunsQueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        query_kwargs: dict = {},
        *args,
        **kwargs,
    ) -> dict:
        if operation == "recurrence":
            return {
                "results": [
                    {"label": "label1", "value": 10, "full_value": 10},
                    {"label": "label2", "value": 20, "full_value": 20},
                ],
            }
        elif operation == "count":
            return {"value": 12}
