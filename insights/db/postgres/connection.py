from contextlib import contextmanager

from django.db import connections
from psycopg.rows import dict_row


def pg_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor(row_factory=dict_row) as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


@contextmanager
def get_cursor(db_name: str):
    with connections[db_name] as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            yield cur
