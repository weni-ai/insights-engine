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
        query = (
            "SELECT u.email, CONCAT(u.first_name, ' ', u.last_name) AS name "
            "FROM public.projects_projectpermission AS pp "
            "INNER JOIN public.accounts_user AS u ON u.email=pp.user_id "
            f"WHERE {self.where_clause} AND pp.is_deleted = false;"
        )

        return query, self.params


class ProjectAdminsAndManagersSQLQueryBuilder(AgentSQLQueryBuilder):
    """
    Same as AgentSQLQueryBuilder, but restricted to users who are either
    project admins (ProjectPermission.role == ROLE_ADMIN) or sector managers
    (SectorAuthorization.role == ROLE_MANAGER) for at least one sector.
    Soft-deleted project permissions are always excluded.
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
            f"ON sa.permission_id=pp.uuid AND sa.role={self.ROLE_MANAGER} "
            f"WHERE {self.where_clause} AND "
            f"(pp.role={self.ROLE_ADMIN} OR sa.role={self.ROLE_MANAGER}) "
            "AND pp.is_deleted = false;"
        )

        return query, self.params
