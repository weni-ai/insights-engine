from insights.sources.base import BaseQueryExecutor
from insights.sources.channels.enums import Channel


class QueryExecutor(BaseQueryExecutor):
    DEFAULT_LIMIT = 20

    @classmethod
    def _unwrap(cls, value, default=None):
        if isinstance(value, list):
            value = value[0] if value else default
        if value in (None, ""):
            return default
        return value

    @classmethod
    def _parse_limit_offset(cls, filters: dict) -> tuple[int, int]:
        try:
            limit = int(cls._unwrap(filters.get("limit"), cls.DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = cls.DEFAULT_LIMIT
        try:
            offset = int(cls._unwrap(filters.get("offset"), 0))
        except (TypeError, ValueError):
            offset = 0

        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return limit, offset

    @classmethod
    def execute(
        cls,
        filters: dict,
        operation: str,
        parser: callable = None,
        query_kwargs: dict = {},
        *args,
        **kwargs,
    ):
        filters = dict(filters or {})
        search = str(cls._unwrap(filters.get("search"), "")).strip().lower()
        limit, offset = cls._parse_limit_offset(filters)

        results = [
            {"uuid": channel.value, "name": channel.label} for channel in Channel
        ]
        if search:
            results = [
                item
                for item in results
                if search in item["uuid"] or search in item["name"].lower()
            ]

        count = len(results)
        page = results[offset : offset + limit]
        next_offset = offset + limit
        previous_offset = max(offset - limit, 0)

        return {
            "count": count,
            "next": next_offset if next_offset < count else None,
            "previous": previous_offset if offset > 0 else None,
            "results": page,
            "limit": limit,
            "offset": offset,
        }
