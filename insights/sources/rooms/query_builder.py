class RoomSQLQueryBuilder:
    def __init__(self):
        self.joins = dict()
        self.where_clauses = []
        self.params = []
        self.is_valid = False

    def add_filter(self, strategy, field, operation, value, table_alias: str = "r"):
        if table_alias == "ctt" and field == "uuid":
            field = {
                "name": "ctt",
                "external_id": "ctt",
                "urn": "r",
            }  # {field_name: table_alias}
            operation = "or"
        clause, params = strategy.apply(field, operation, value, table_alias)

        self.where_clauses.append(clause)
        if params is not None:
            self.params.extend(params)

    def add_joins(self, joins: set):
        self.joins.update(joins)

    def build_query(self):
        self.join_clause = " ".join(self.joins.values())
        self.where_clause = " AND ".join(self.where_clauses)
        self.is_valid = True

    def timeseries_hour_group_count(
        self, time_field: str = "created_on", limit: int = 24, *args, **kwargs
    ):
        if not self.is_valid:
            self.build_query()
        query = f"WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.{time_field} AT TIME ZONE '{timezone}') AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause} GROUP BY hour) SELECT CONCAT(hours.label, 'h') AS label, COALESCE(hourly_data.rooms_count, 0) AS value FROM generate_series(0, 23) AS hours(label) LEFT JOIN hourly_data ON hours.label::int = hourly_data.hour ORDER BY value DESC FETCH FIRST {limit} ROWS ONLY;"
        return query, self.params

    def count(self, *args, **kwargs):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT COUNT(r.*) AS value FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause};"

        return query, self.params

    def sum(self, op_field: str, *args, **kwargs):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT SUM(mr.{op_field}) AS value FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid {self.join_clause} WHERE {self.where_clause};"

        return query, self.params

    def avg(self, op_field: str, *args, **kwargs):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT (ROUND(COALESCE(AVG(mr.{op_field}), 0)/60, 2)) AS value FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid {self.join_clause} WHERE {self.where_clause};"

        return query, self.params
