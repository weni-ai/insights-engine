class FlowSQLQueryBuilder:
    def __init__(self):
        self.joins = dict()
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_joins(self, joins: set):
        self.joins.update(joins)

    def add_filter(self, strategy, field, operation, value, table_alias: str = "f"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def build_query(self):
        self.join_clause = " ".join(self.joins.values())
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT f.uuid, f.name FROM public.flows_flow AS f {self.join_clause} WHERE {self.where_clause};"

        return query, self.params
