from django.db import connections


def secondary_dbs_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


# TODO: VERIFY IF THERE'S A POSSIBILITY OF SQL INJECTION IN THIS FUNCTION, and, if there is, treat it!
def sql_filter_dict_parser(filters: dict):
    keys = []
    values = []
    key_position = 1
    for key, value in filters.items():
        prefix = ""
        if key_position != 1:
            prefix = " AND "

        if key.endswith("__after"):
            sql_key = key.split("_")[0] + " > (%s)"
            values.append(value)
        elif key.endswith("__before"):
            sql_key = key.split("__")[0] + " < (%s)"
            values.append(value)
        elif type(value) is list:
            placeholders = ", ".join(["%s"] * len(value))
            sql_key = f"{key} IN ({placeholders})"
            values += value
        else:
            sql_key = key + " = (%s)"
            values.append(value)

        keys.append(prefix + sql_key)

        key_position += 1

    return filters.keys, filters.values


def room_field_check(field): ...


def room_sql_filter_relations_parser(filters: dict):
    for field, value in filters.items():
        ...


"""
CONVERTER FILTRO JSON PARA SQL JSON, CRIANDO OS JOINS E ADICIONANDO ALIAS QUANDO NECESSÁRIOS
"""


join_dict = {
    "sector": {
        "join": "INNER JOIN public.queues_queue as q ON q.uuid=queue_id",
        "alias": "q",
        "sqlfield": "q.sector_id",
    },
    "project": {
        "join": "INNER JOIN public.sectors_sector as s ON s.uuid=q.sector_id",
        "alias": "s",
        "sqlfield": "s.project_id",
    },
    "user": {
        "join": "INNER JOIN public.accounts_user as u ON u.email=user_id",
        "alias": "u",
        "sqlfield": "",
    },
    "tags": {"join": None, "alias": "tags"},
}


# FILTERS CANNOT BE NULL!!!!
class RoomPGClient:
    def __init__(self) -> None:
        self.db_name = "chats"
        self.filter_parser = sql_filter_dict_parser

    def timeseries_hour_group_count(
        self, filters: dict, time_field: str, limit: int = 24
    ):
        joins, placeholders, values = self.filter_parser(filters)
        list_room_timeseries_by_hour_sql = f"WITH hourly_data AS(SELECT EXTRACT( HOUR FROM r.{time_field}) AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r {joins} WHERE {placeholders} GROUP BY hour) SELECT hours.hour, COALESCE(hourly_data.rooms_count, 0) FROM generate_series(0, 23) AS hours(hour) LEFT JOIN hourly_data ON hours.hour = hourly_data.hour ORDER BY rooms_created DESC FETCH FIRST {limit} ROWS ONLY;"

        return secondary_dbs_execute_query(
            db_name=self.db_name, query=list_room_timeseries_by_hour_sql, args=values
        )

    def count(self, filters: dict):
        joins, placeholders, values = self.filter_parser(filters)
        count_sql = (
            f"SELECT COUNT(*) FROM public.rooms_room {joins} WHERE {placeholders};"
        )

        return secondary_dbs_execute_query(
            db_name=self.db_name, query=count_sql, args=values
        )

    def sum(self, filters: dict, sum_field: str):
        joins, placeholders, values = self.filter_parser(filters)
        count_sql = f"""SELECT SUM(mr.{sum_field}) FROM public.rooms_room INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=uuid", "alias": "mr" {joins} WHERE {placeholders};"""

        return secondary_dbs_execute_query(
            db_name=self.db_name, query=count_sql, args=values
        )

    def avg(self, filters: dict, sum_field: str):
        joins, placeholders, values = self.filter_parser(filters)
        count_sql = f"""SELECT AVG(mr.{sum_field}) FROM public.rooms_room INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=uuid", "alias": "mr" {joins} WHERE {placeholders};"""

        return secondary_dbs_execute_query(
            db_name=self.db_name, query=count_sql, args=values
        )
