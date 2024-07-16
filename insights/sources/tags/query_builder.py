class TagSQLQueryBuilder:
    def __init__(self):
        self.joins = dict()
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "tg"):
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
        query = f"SELECT tg.uuid,tg.name FROM public.sectors_sectortag AS tg {self.join_clause} WHERE {self.where_clause};"

        return query, self.params
