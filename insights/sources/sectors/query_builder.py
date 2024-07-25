class SectorSQLQueryBuilder:
    def __init__(self):
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "s"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def build_query(self):
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT s.uuid,s.name FROM public.sectors_sector AS s WHERE {self.where_clause} AND is_deleted=false;"

        return query, self.params
