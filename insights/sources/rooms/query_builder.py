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
            if type(value) is list:
                value = value[0]
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
        self,
        time_field: str = "created_on",
        limit: int = 24,
        timezone: str = "UTC",
        *args,
        **kwargs,
    ):
        time_range = (kwargs.get("start_hour", 0), kwargs.get("end_hour", 23))

        if not self.is_valid:
            self.build_query()
        query = f"WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.{time_field} AT TIME ZONE '{timezone}') AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause} GROUP BY hour) SELECT CONCAT(hours.label, 'h') AS label, COALESCE(hourly_data.rooms_count, 0) AS value FROM generate_series({time_range[0]}, {time_range[1]}) AS hours(label) LEFT JOIN hourly_data ON hours.label::int = hourly_data.hour ORDER BY value DESC FETCH FIRST {limit} ROWS ONLY;"
        return query, self.params

    def timeseries_day_group_count(
        self,
        time_field: str = "created_on",
        timezone: str = "UTC",
        *args,
        **kwargs,
    ):
        if not self.is_valid:
            self.build_query()
        query = f"SELECT DATE(r.{time_field} AT TIME ZONE '{timezone}') AS label, COUNT(*) AS value FROM public.rooms_room as r {self.join_clause} WHERE {self.where_clause} GROUP BY DATE(r.{time_field} AT TIME ZONE '{timezone}') ORDER BY label ASC;"
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
        query = f"SELECT (ROUND(COALESCE(AVG(mr.{op_field}), 0), 2)) AS value FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid {self.join_clause} WHERE {self.where_clause};"

        return query, self.params

    def group_by_queue_count(self, limit: int = 5, *args, **kwargs):
        """
        Groups rooms by queue, organized by sector.
        Returns: sector_uuid, sector_name, queue_uuid, queue_name, value (count)
        Sorted by value DESC, then queue_name ASC (alphabetical tie-breaker)
        """
        if not self.is_valid:
            self.build_query()

        # Ensures that the join with queues_queue and sectors_sector exists (aliases q and sec)
        queue_join = """
            INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id AND q.is_deleted=false
            INNER JOIN public.sectors_sector AS sec ON sec.uuid=q.sector_id AND sec.is_deleted=false
        """
        sector_as_sec_join = """
            INNER JOIN public.sectors_sector AS sec ON sec.uuid=q.sector_id AND sec.is_deleted=false
        """
        if "q" not in self.joins:
            self.join_clause = f"{queue_join} {self.join_clause}"
        elif "sec" not in self.joins:
            # Filters use alias "s" for sector; this query uses "sec" — add sec so SELECT is valid
            self.join_clause = f"{sector_as_sec_join} {self.join_clause}"

        query = f"""
            SELECT
                sec.uuid AS sector_uuid,
                sec.name AS sector_name,
                q.uuid AS queue_uuid,
                q.name AS queue_name,
                COUNT(r.*) AS value
            FROM public.rooms_room AS r
            {self.join_clause}
            WHERE {self.where_clause}
            GROUP BY sec.uuid, sec.name, q.uuid, q.name
            ORDER BY value DESC, queue_name ASC;
        """
        return query, self.params

    def group_by_tag_count(self, limit: int = 5, *args, **kwargs):
        """
        Groups rooms by tag, organized by sector.
        Returns: sector_uuid, sector_name, tag_uuid, tag_name, value (count)
        Sorted by value DESC, then tag_name ASC (alphabetical tie-breaker)
        """
        if not self.is_valid:
            self.build_query()

        # Ensures that joins with rooms_room_tags, sectors_sectortag and sectors_sector exist
        tag_joins = """
            INNER JOIN public.rooms_room_tags AS rt ON rt.room_id=r.uuid
            INNER JOIN public.sectors_sectortag AS stg ON stg.uuid=rt.sectortag_id
            INNER JOIN public.sectors_sector AS sec ON sec.uuid=stg.sector_id AND sec.is_deleted=false
        """

        query = f"""
            SELECT
                sec.uuid AS sector_uuid,
                sec.name AS sector_name,
                stg.uuid AS tag_uuid,
                stg.name AS tag_name,
                COUNT(DISTINCT r.uuid) AS value
            FROM public.rooms_room AS r
            {tag_joins}
            {self.join_clause}
            WHERE {self.where_clause}
            GROUP BY sec.uuid, sec.name, stg.uuid, stg.name
            ORDER BY value DESC, tag_name ASC;
        """
        return query, self.params
