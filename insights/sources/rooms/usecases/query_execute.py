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
from insights.sources.base import BaseQueryExecutor
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder


class QueryExecutor(BaseQueryExecutor):
    @classmethod
    def execute(
        cls,
        filters: dict,
        operation: str,
        parser: callable,
        project: object,
        query_kwargs: dict = {},
        *args,
        **kwargs
    ):
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
            return paginated_results  # parser(paginated_results)

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
        elif operation == "timeseries_day_group_count":
            paginated_results = {
                "next": None,
                "previous": None,
                "results": query_results,
            }
        elif operation == "group_by_queue_count":
            grouped = {}
            for row in query_results:
                sector_uuid = row["sector_uuid"]
                if sector_uuid not in grouped:
                    sector_name = row["sector_name"]
                    sector_is_deleted = row["sector_is_deleted"]

                    if sector_is_deleted and "_is_deleted_" in sector_name:
                        sector_name = sector_name.split("_is_deleted_")[0]

                    grouped[sector_uuid] = {
                        "sector_name": sector_name,
                        "is_deleted": sector_is_deleted,
                        "queues": [],
                    }

                queue_name = row["queue_name"]
                queue_is_deleted = row["queue_is_deleted"]

                if queue_is_deleted and "_is_deleted_" in queue_name:
                    queue_name = queue_name.split("_is_deleted_")[0]

                grouped[sector_uuid]["queues"].append(
                    {
                        "queue_name": queue_name,
                        "is_deleted": queue_is_deleted,
                        "value": row["value"],
                    }
                )

            results = sorted(
                grouped.values(),
                key=lambda sector: sum(queue["value"] for queue in sector["queues"]),
                reverse=True,
            )
            total_queues = sum(len(sector["queues"]) for sector in results)

            paginated_results = {
                "next": None,
                "previous": None,
                "count": total_queues,
                "results": results,
            }
        elif operation == "group_by_tag_count":
            grouped = {}
            for row in query_results:
                sector_uuid = row["sector_uuid"]
                if sector_uuid not in grouped:
                    sector_name = row["sector_name"]
                    sector_is_deleted = row["sector_is_deleted"]

                    if sector_is_deleted and "_is_deleted_" in sector_name:
                        sector_name = sector_name.split("_is_deleted_")[0]

                    grouped[sector_uuid] = {
                        "sector_name": sector_name,
                        "is_deleted": sector_is_deleted,
                        "tags": [],
                    }

                tag_name = row["tag_name"]
                tag_is_deleted = row["tag_is_deleted"]

                if tag_is_deleted and "_is_deleted_" in tag_name:
                    tag_name = tag_name.split("_is_deleted_")[0]

                grouped[sector_uuid]["tags"].append(
                    {
                        "tag_name": tag_name,
                        "is_deleted": tag_is_deleted
                        or grouped[sector_uuid]["is_deleted"],
                        "value": row["value"],
                    }
                )

            results = sorted(
                grouped.values(),
                key=lambda sector: sum(tag["value"] for tag in sector["tags"]),
                reverse=True,
            )
            total_tags = sum(len(sector["tags"]) for sector in results)

            paginated_results = {
                "next": None,
                "previous": None,
                "count": total_tags,
                "results": results,
            }
        else:
            paginated_results = {
                "next": None,
                "previous": None,
                "results": query_results,
            }
        return paginated_results
