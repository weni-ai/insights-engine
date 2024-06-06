from django.db import connections


def secondary_dbs_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


class RoomSQLQueryBuilder:
    def __init__(self):
        self.joins = dict()
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "r"):
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        self.params.extend(params)

    def add_joins(self, joins: set):
        self.joins.update(joins)

    def build_query(self):
        self.join_clause = " ".join(self.joins.values())
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def timeseries_hour_group_count(
        self, time_field: str = "created_on", limit: int = 24
    ):
        if not self.is_valid:
            self.build_query()
        query = f"WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.{time_field}) AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause} GROUP BY hour) SELECT hours.hour, COALESCE(hourly_data.rooms_count, 0) AS rooms_created FROM generate_series(0, 23) AS hours(hour) LEFT JOIN hourly_data ON hours.hour = hourly_data.hour ORDER BY rooms_created DESC FETCH FIRST {limit} ROWS ONLY;"

        return query, self.params

    def count(self):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT COUNT(r.*) FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause};"

        return query, self.params

    def sum(self, field_name: str):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT SUM(mr.{field_name}) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid {self.join_clause} WHERE {self.where_clause};"

        return query, self.params

    def avg(self, field_name: str):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT AVG(mr.{field_name}) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid {self.join_clause} WHERE {self.where_clause};"

        return query, self.params
