from insights.db.postgres.django.connection import (
    dictfetchall,
    dictfetchone,
    get_cursor,
)
from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.rooms.clients import (
    RoomRESTClient,
    RoomSQLQueryGenerator,
)
from insights.sources.rooms.filtersets import RoomFilterSet
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder


class QueryExecutor:
    def execute(
        filters: dict,
        operation: str,
        parser: callable,
        project: object,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
        # Adiciona filtro para excluir rooms importadas em todas as consultas
        filters = filters.copy()  # Não modifica o original
        filters["imported_room__ne"] = True
        
        if operation == "list":
            client = RoomRESTClient(project=project)
            query_results = client.list(filters)
            nxt = query_results.get("next")
            nxt = None if nxt is None else nxt.split("?")[1]
            prev = query_results.get("previous")
            prev = None if prev is None else prev.split("?")[1]
            count = query_results.get("count", 0)
            paginated_results = {
                "next": nxt,
                "previous": prev,
                "count": count,
                "results": query_results.get("results", []),
            }
            return paginated_results

        query_generator = RoomSQLQueryGenerator(
            filter_strategy=PostgreSQLFilterStrategy,
            query_builder=RoomSQLQueryBuilder,
            filterset=RoomFilterSet,
            filters=filters,
            query_type=operation,
            query_kwargs=query_kwargs,
        )
        query, params = query_generator.generate()
        with get_cursor(db_name="chats") as cur:
            query_exec = cur.execute(query, params)
            if operation in ["count", "avg"]:
                query_results = dictfetchone(query_exec)
            else:
                query_results = dictfetchall(query_exec)

        if operation in ["count", "avg"]:
            paginated_results = query_results
        elif operation == "timeseries_hour_group_count":
            paginated_results = {
                "next": None,
                "previous": None,
                "results": sorted(query_results, key=lambda x: int(x["label"][:-1])),
            }
        else:
            paginated_results = {
                "next": None,
                "previous": None,
                "results": query_results,
            }
        return paginated_results  # parser(paginated_results)
