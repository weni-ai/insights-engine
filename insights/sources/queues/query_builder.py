from django.db import connections


def secondary_dbs_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


class QueueSQLQueryBuilder:
    def __init__(self):
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "r"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def build_query(self):
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def list(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT q.uuid,q.name FROM public.queues_queue AS q INNER JOIN public.sectors_sector AS s ON s.uuid == q.sector_id WHERE {self.where_clause};"

        return query, self.params
