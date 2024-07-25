class QueueSQLQueryBuilder:
    def __init__(self):
        self.joins = dict()
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "q"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def add_joins(self, joins: set):
        self.joins.update(joins)

    def build_query(self):
        self.where_clause = " AND ".join(self.where_clauses)
        self.join_clause = " ".join(self.joins.values())

        self.is_valid = True

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT q.uuid,q.name FROM public.queues_queue AS q {self.join_clause} WHERE {self.where_clause} AND is_deleted=false;"

        return query, self.params
