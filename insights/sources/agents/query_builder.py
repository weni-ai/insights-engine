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

    def list(self, include_removed=False):
        if not self.is_valid:
            self.build_query()
        extra_clause = ""
        extra_params = []
        if not include_removed:
            extra_clause = " AND pp.is_deleted = %s"
            extra_params = [False]
        query = f"SELECT u.email, CONCAT(u.first_name, ' ', u.last_name) AS name FROM public.projects_projectpermission AS pp INNER JOIN public.accounts_user AS u ON u.email=pp.user_id WHERE {self.where_clause}{extra_clause};"

        return query, self.params + extra_params


class ProjectAdminsAndManagersSQLQueryBuilder(AgentSQLQueryBuilder):
    """
    Same as AgentSQLQueryBuilder, but restricted to users who are either
    project admins (ProjectPermission.role == ROLE_ADMIN) or sector managers
    (SectorAuthorization.role == ROLE_MANAGER) for at least one sector.
    """

    ROLE_ADMIN = 1
    ROLE_MANAGER = 1

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = (
            "SELECT DISTINCT u.email, "
            "CONCAT(u.first_name, ' ', u.last_name) AS name "
            "FROM public.projects_projectpermission AS pp "
            "INNER JOIN public.accounts_user AS u ON u.email=pp.user_id "
            "LEFT JOIN public.sectors_sectorauthorization AS sa "
            f"ON sa.permission_id=pp.id AND sa.role={self.ROLE_MANAGER} "
            f"WHERE {self.where_clause} AND (pp.role={self.ROLE_ADMIN} OR sa.role={self.ROLE_MANAGER});"
        )

        return query, self.params
