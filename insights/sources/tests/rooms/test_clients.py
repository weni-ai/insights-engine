# from insights.sources.rooms.clients import (
#     generate_sql_query,
#     get_joins_from_schema,
# )


# def test_generate_sql_query_count():
#     filter_dict = {"user_id": 123}
#     query, params = generate_sql_query(filter_dict)
#     expected_query = (
#         "SELECT COUNT(r.*) FROM public.rooms_room as r  WHERE r.user_id = (%s);"
#     )
#     assert query == expected_query
#     assert params == [123]


# def test_generate_sql_query_timeseries():
#     filter_dict = {"user_id": 123}
#     query, params = generate_sql_query(
#         filter_dict, query_type="timeseries_hour_group_count"
#     )
#     expected_query = "WITH hourly_data AS (SELECT EXTRACT(HOUR FROM r.created_on) AS hour, COUNT(*) AS rooms_count FROM public.rooms_room as r  WHERE r.user_id = (%s) GROUP BY hour) SELECT hours.hour, COALESCE(hourly_data.rooms_count, 0) AS rooms_created FROM generate_series(0, 23) AS hours(hour) LEFT JOIN hourly_data ON hours.hour = hourly_data.hour ORDER BY rooms_created DESC FETCH FIRST 24 ROWS ONLY;"
#     assert query == expected_query
#     assert params == [123]


# def test_generate_sql_query_sum():
#     filter_dict = {"user_id": 123}
#     query, params = generate_sql_query(
#         filter_dict, query_type="sum", query_kwargs={"op_field": "duration"}
#     )
#     expected_query = "SELECT SUM(mr.duration) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
#     assert query == expected_query
#     assert params == [123]


# def test_generate_sql_query_avg():
#     filter_dict = {"user_id": 123}
#     query, params = generate_sql_query(
#         filter_dict, query_type="avg", query_kwargs={"op_field": "duration"}
#     )
#     expected_query = "SELECT AVG(mr.duration) FROM public.rooms_room as r INNER JOIN public.dashboard_roommetrics AS mr ON mr.room_id=r.uuid  WHERE r.user_id = (%s);"
#     assert query == expected_query
#     assert params == [123]


# def test_generate_sql_query_with_operation():
#     filter_dict = {"user_id": 123, "ended_at__before": "2024-03-21"}
#     query, params = generate_sql_query(filter_dict)
#     expected_query = "SELECT COUNT(r.*) FROM public.rooms_room as r  WHERE r.user_id = (%s) AND r.ended_at < (%s);"
#     assert query == expected_query
#     assert params == [123, "2024-03-21"]


# def test_generate_sql_query_with_tag_join():
#     filter_dict = {"user_id": 123, "tag__in": [1, 2, 3, 4]}
#     query, params = generate_sql_query(filter_dict)
#     expected_query = "SELECT COUNT(r.*) FROM public.rooms_room as r INNER JOIN public.rooms_room_tags AS tg ON tg.room_id=r.uuid WHERE r.user_id = (%s) AND tg.sectortag_id IN (%s, %s, %s, %s);"
#     assert query == expected_query
#     assert params == [123, 1, 2, 3, 4]


# def test_generate_sql_query_with_project_join():
#     filter_dict = {"user_id": 123, "project": "asd"}
#     query, params = generate_sql_query(filter_dict)

#     assert "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id" in query
#     assert "INNER JOIN public.projects_project AS p ON p.uuid=s.project_id" in query
#     assert "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id" in query
#     assert query.endswith("WHERE r.user_id = (%s) AND p.uuid = (%s);")
#     assert params == [123, "asd"]


# def test_get_joins_from_schema():
#     assert get_joins_from_schema("sector") == {
#         "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id"
#     }
#     assert get_joins_from_schema("project") == {
#         "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id",
#         "s": "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id",
#         "p": "INNER JOIN public.projects_project AS p ON p.uuid=s.project_id",
#     }
#     assert get_joins_from_schema("tag") == {
#         "tg": "INNER JOIN public.rooms_room_tags AS tg ON tg.room_id=r.uuid"
#     }
#     assert get_joins_from_schema("other_field") == dict()
