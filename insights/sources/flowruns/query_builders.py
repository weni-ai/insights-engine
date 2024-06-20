class FlowRunsElasticSearchQueryBuilder:
    def __init__(self):
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "s"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def build_query(self):
        self.where_clause.join(self.where_clauses)
        self.is_valid = True

    def count(self) -> list[str, dict]:
        """return endpoint and filter"""
        return ["_count", {"query": self.where_clauses}]

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
        return ["_search", {"size": 0, "query": self.where_clauses, "aggs": aggs}]

    def sum(self, op_field):
        return self._base_operation("sum", op_field)

    def avg(self, op_field):
        return self._base_operation("avg", op_field)

    def max(self, op_field):
        return self._base_operation("max", op_field)

    def min(self, op_field):
        return self._base_operation("min", op_field)

    def recurrence(self, op_field):
        return self._base_operation("min", op_field, "values.value")
