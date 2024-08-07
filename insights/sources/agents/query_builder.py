class AgentSQLQueryBuilder:
    def __init__(self):
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "pp"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def build_query(self):
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT pp.uuid, u.email, CONCAT(u.first_name, ' ', u.last_name) AS name FROM public.projects_projectpermission AS pp INNER JOIN public.accounts_user AS u ON u.email=pp.user_id WHERE {self.where_clause};"

        return query, self.params
