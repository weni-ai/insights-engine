import logging
from contextlib import contextmanager

from django.conf import settings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, NullConnectionPool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logging.getLogger("psycopg.pool").setLevel(logging.INFO)

pools = {}


@contextmanager
def get_connection(db_name: str):
    if not pools.get(db_name, None):
        pools[db_name] = NullConnectionPool(
            max_size=5,
            conninfo=settings.DATABASES.get(db_name),
            check=ConnectionPool.check_connection,
        )
    with pools.get(db_name).connection() as conn:
        yield conn


@contextmanager
def get_cursor(db_name: str):
    with get_connection(db_name) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            yield cur
