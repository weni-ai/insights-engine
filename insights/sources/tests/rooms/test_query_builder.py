from django.test import TestCase

from insights.sources.filter_strategies import PostgreSQLFilterStrategy
from insights.sources.rooms.query_builder import RoomSQLQueryBuilder


class TestRoomSQLQueryBuilder(TestCase):
    def setUp(self):
        self.strategy = PostgreSQLFilterStrategy()
        self.builder = RoomSQLQueryBuilder()

    def test_add_filter(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        self.assertEqual(self.builder.where_clauses, ["r.user_id = (%s)"])
        self.assertEqual(self.builder.params, [123])

    def test_add_filter_with_table_alias(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123, table_alias="u")
        self.assertEqual(self.builder.where_clauses, ["u.user_id = (%s)"])
        self.assertEqual(self.builder.params, [123])

    def test_add_filter_with_ctt_alias_and_uuid_field(self):
        self.builder.add_filter(
            self.strategy, "uuid", "eq", ["test_uuid"], table_alias="ctt"
        )
        expected_clause = (
            "(ctt.name ILIKE (%s) OR ctt.external_id ILIKE (%s) OR r.urn ILIKE (%s))"
        )
        self.assertEqual(self.builder.where_clauses, [expected_clause])
        expected_params = [f"%{p}%" for p in ["test_uuid"] * 3]
        self.assertEqual(self.builder.params, expected_params)

    def test_add_filter_with_ctt_alias_uuid_field_and_string_value(self):
        self.builder.add_filter(
            self.strategy, "uuid", "eq", "test_uuid_str", table_alias="ctt"
        )
        expected_clause = (
            "(ctt.name ILIKE (%s) OR ctt.external_id ILIKE (%s) OR r.urn ILIKE (%s))"
        )
        self.assertEqual(self.builder.where_clauses, [expected_clause])
        expected_params = [f"%{p}%" for p in ["test_uuid_str"] * 3]
        self.assertEqual(self.builder.params, expected_params)

    def test_add_joins(self):
        joins = {"u": "INNER JOIN users u ON u.id = r.user_id"}
        self.builder.add_joins(joins)
        self.assertEqual(self.builder.joins, joins)

    def test_build_query(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        self.builder.build_query()
        self.assertEqual(self.builder.join_clause, "")
        self.assertEqual(self.builder.where_clause, "r.user_id = (%s)")
        self.assertTrue(self.builder.is_valid)

    def test_timeseries_hour_group_count(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        query, params = self.builder.timeseries_hour_group_count()
        expected_query = "WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.created_on AT TIME ZONE 'UTC') AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r  WHERE r.user_id = (%s) GROUP BY hour) SELECT CONCAT(hours.label, 'h') AS label, COALESCE(hourly_data.rooms_count, 0) AS value FROM generate_series(0, 23) AS hours(label) LEFT JOIN hourly_data ON hours.label::int = hourly_data.hour ORDER BY value DESC FETCH FIRST 24 ROWS ONLY;"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, [123])

    def test_count(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        query, params = self.builder.count()
        expected_query = "SELECT COUNT(r.*) AS value FROM public.rooms_room as r  WHERE r.user_id = (%s);"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, [123])

    def test_sum(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        query, params = self.builder.sum("duration")
        expected_query = "SELECT SUM(mr.duration) AS value FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, [123])

    def test_avg(self):
        self.builder.add_filter(self.strategy, "user_id", "eq", 123)
        query, params = self.builder.avg("duration")
        expected_query = "SELECT (ROUND(COALESCE(AVG(mr.duration), 0), 2)) AS value FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, [123])
