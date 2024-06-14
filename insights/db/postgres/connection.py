from contextlib import contextmanager

import settings
from psycopg import connect
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, NullConnectionPool


def dictfetchall(cursor):
    return cursor.fetchall()


def dictfetchone(cursor):
    return cursor.fetchone()


chats_pool = NullConnectionPool(
    max_size=5,
    conninfo=settings.CHATS_PG,
    check=ConnectionPool.check_connection,
)


@contextmanager
def get_connection():
    # if settings.CONNECTION_TYPE == "pool":
    #     with chats_pool.connection() as conn:
    #         yield conn
    # else:
    with connect(settings.CHATS_PG) as conn:
        yield conn


@contextmanager
def get_cursor(*args, **kwargs):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            yield cur
