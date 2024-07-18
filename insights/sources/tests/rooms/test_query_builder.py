import pytest

from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder


@pytest.fixture
def strategy():
    return PostgreSQLFilterStrategy()


@pytest.fixture
def builder():
    return RoomSQLQueryBuilder()


def test_add_filter(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    assert builder.where_clauses == ["r.user_id = (%s)"]
    assert builder.params == [123]


def test_add_filter_with_table_alias(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123, table_alias="u")
    assert builder.where_clauses == ["u.user_id = (%s)"]
    assert builder.params == [123]


def test_add_joins(builder):
    joins = {"u": "INNER JOIN users u ON u.id = r.user_id"}
    builder.add_joins(joins)
    assert builder.joins == joins


def test_build_query(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    builder.build_query()
    assert builder.join_clause == ""
    assert builder.where_clause == "r.user_id = (%s)"
    assert builder.is_valid is True


def test_timeseries_hour_group_count(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    query, params = builder.timeseries_hour_group_count()
    expected_query = "WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.created_on) AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r  WHERE r.user_id = (%s) GROUP BY hour) SELECT hours.hour, COALESCE(hourly_data.rooms_count, 0) AS rooms_created FROM generate_series(0, 23) AS hours(hour) LEFT JOIN hourly_data ON hours.hour = hourly_data.hour ORDER BY rooms_created DESC FETCH FIRST 24 ROWS ONLY;"
    assert query == expected_query
    assert params == [123]


def test_count(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    query, params = builder.count()
    expected_query = (
        "SELECT COUNT(r.*) FROM public.rooms_room as r  WHERE r.user_id = (%s);"
    )
    assert query == expected_query
    assert params == [123]


def test_sum(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    query, params = builder.sum("duration")
    expected_query = "SELECT SUM(mr.duration) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
    assert query == expected_query
    assert params == [123]


def test_avg(strategy, builder):
    builder.add_filter(strategy, "user_id", "eq", 123)
    query, params = builder.avg("duration")
    expected_query = "SELECT AVG(mr.duration) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
    assert query == expected_query
    assert params == [123]
