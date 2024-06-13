from contextlib import contextmanager

from django.db import connections


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return results if len(results) > 1 else results[0]


def pg_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args).fetchall()


@contextmanager
def get_cursor(db_name: str):
    with connections[db_name].cursor() as cur:
        yield cur
