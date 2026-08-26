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


def _strip_deleted_suffix(name: str, is_deleted: bool) -> str:
    if is_deleted and "_is_deleted_" in name:
        return name.split("_is_deleted_")[0]
    return name


class QueryExecutor(BaseQueryExecutor):
    @classmethod
    def _get_list_operation_results(cls, project: object, filters: dict) -> dict:
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

    @classmethod
    def _get_sql_operation_results(
        cls, filters: dict, operation: str, query_kwargs: dict
    ) -> dict:
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

        return query_results

    @classmethod
    def _format_timeseries_hour(cls, query_results):
        return {
            "next": None,
            "previous": None,
            "results": sorted(query_results, key=lambda x: int(x["label"][:-1])),
        }

    @classmethod
    def _format_timeseries_day(cls, query_results):
        return {
            "next": None,
            "previous": None,
            "results": query_results,
        }

    @classmethod
    def _format_group_by_queue(cls, query_results):
        grouped = {}
        for row in query_results:
            sector_uuid = row["sector_uuid"]
            if sector_uuid not in grouped:
                grouped[sector_uuid] = {
                    "sector_name": _strip_deleted_suffix(
                        row["sector_name"], row["sector_is_deleted"]
                    ),
                    "is_deleted": row["sector_is_deleted"],
                    "queues": [],
                }

            grouped[sector_uuid]["queues"].append(
                {
                    "queue_name": _strip_deleted_suffix(
                        row["queue_name"], row["queue_is_deleted"]
                    ),
                    "is_deleted": row["queue_is_deleted"],
                    "value": row["value"],
                }
            )

        results = sorted(
            grouped.values(),
            key=lambda sector: sum(queue["value"] for queue in sector["queues"]),
            reverse=True,
        )
        total_queues = sum(len(sector["queues"]) for sector in results)

        return {
            "next": None,
            "previous": None,
            "count": total_queues,
            "results": results,
        }

    @classmethod
    def _format_group_by_tag(cls, query_results):
        grouped = {}
        for row in query_results:
            sector_uuid = row["sector_uuid"]
            if sector_uuid not in grouped:
                grouped[sector_uuid] = {
                    "sector_name": _strip_deleted_suffix(
                        row["sector_name"], row["sector_is_deleted"]
                    ),
                    "is_deleted": row["sector_is_deleted"],
                    "tags": [],
                }

            tag_is_deleted = row["tag_is_deleted"]
            grouped[sector_uuid]["tags"].append(
                {
                    "tag_name": _strip_deleted_suffix(
                        row["tag_name"], tag_is_deleted
                    ),
                    "is_deleted": tag_is_deleted or grouped[sector_uuid]["is_deleted"],
                    "value": row["value"],
                }
            )

        results = sorted(
            grouped.values(),
            key=lambda sector: sum(tag["value"] for tag in sector["tags"]),
            reverse=True,
        )
        total_tags = sum(len(sector["tags"]) for sector in results)

        return {
            "next": None,
            "previous": None,
            "count": total_tags,
            "results": results,
        }

    @classmethod
    def _format_group_by_channel(cls, query_results):
        results = [
            {
                "channel_name": row["channel_name"],
                "rooms_volume": row["rooms_volume"],
            }
            for row in query_results
        ]
        return {
            "next": None,
            "previous": None,
            "count": len(results),
            "results": results,
        }

    @classmethod
    def _format_default(cls, query_results):
        return {
            "next": None,
            "previous": None,
            "results": query_results,
        }

    @classmethod
    def _format_sql_results(cls, operation: str, query_results):
        if operation in ["count", "avg"]:
            return query_results

        formatters = {
            "timeseries_hour_group_count": cls._format_timeseries_hour,
            "timeseries_day_group_count": cls._format_timeseries_day,
            "group_by_queue_count": cls._format_group_by_queue,
            "group_by_tag_count": cls._format_group_by_tag,
            "group_by_channel_count": cls._format_group_by_channel,
        }
        formatter = formatters.get(operation, cls._format_default)
        return formatter(query_results)

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
            return cls._get_list_operation_results(project, filters)

        query_results = cls._get_sql_operation_results(filters, operation, query_kwargs)
        return cls._format_sql_results(operation, query_results)
