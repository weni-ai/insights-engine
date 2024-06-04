from django.db import connections


def secondary_dbs_execute_query(db_name: str, query: str, *args, **kwargs):
    with connections[db_name].cursor() as cursor:
        return cursor.execute(query, args, kwargs).fetchall()


class AgentPGQuery:
    def __init__(self) -> None:
        self.db_name = "chats"

    def filter(
        self,
    ): ...
