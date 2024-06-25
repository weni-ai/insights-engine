class FlowRunsElasticSearchQueryBuilder:
    def __init__(self):
        self.query_clauses = {}
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, *args, **kwargs):
        filter_name, filter_value, query_block, query_operation = strategy.apply(
            field, operation, value
        )
        if not self.query_clauses.get(query_block):
            self.query_clauses[query_block] = {}
        if not self.query_clauses[query_block].get(query_operation):
            self.query_clauses[query_block][query_operation] = {}
        if not self.query_clauses[query_block][query_operation].get(filter_name):
            self.query_clauses[query_block][query_operation][filter_name] = filter_value
        else:
            if query_operation == "range":
                self.query_clauses[query_block][query_operation][filter_name].update(
                    filter_value
                )

    def build_query(self):
        query_bool_blocks = {}
        for block, operations in self.query_clauses.items():
            query_bool_blocks[block] = []
            for op, filters in operations.items():
                for fil, value in filters.items():
                    query_bool_blocks[block].append({op: {fil: value}})
        self.validated_query = {"bool": query_bool_blocks}
        self.is_valid = True

    def count(self) -> list[str, dict]:
        """return endpoint and filter"""
        return ["_count", {"query": self.validated_query}]

    def _base_operation(
        self, operation: str, op_field: str, value_field: str = "values.value_number"
    ):
        aggs = {
            "values": {
                "nested": {"path": "values"},
                "aggs": {
                    "agg_field": {
                        "filter": {
                            "bool": {"filter": [{"term": {"values.name": op_field}}]}
                        },
                        "aggs": {"agg_value": {operation: {"field": value_field}}},
                    }
                },
            }
        }
        return ["_search", {"size": 0, "query": self.validated_query, "aggs": aggs}]

    def sum(self, op_field):
        return self._base_operation("sum", op_field)

    def avg(self, op_field):
        return self._base_operation("avg", op_field)

    def max(self, op_field):
        return self._base_operation("max", op_field)

    def min(self, op_field):
        return self._base_operation("min", op_field)

    def recurrence(self, op_field):
        aggs = {
            "values": {
                "nested": {"path": "values"},
                "aggs": {
                    "agg_field": {
                        "filter": {
                            "bool": {"filter": [{"term": {"values.name": op_field}}]}
                        },
                        "aggs": {
                            "agg_value": {
                                "terms": {"size": 100, "field": "values.value"}
                            }
                        },
                    }
                },
            }
        }
        return ["_search", {"size": 0, "query": self.validated_query, "aggs": aggs}]
