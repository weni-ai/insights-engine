from django.test import TestCase

from insights.sources.channels.enums import Channel
from insights.sources.channels.usecases.query_execute import QueryExecutor


class TestChannelQueryExecutor(TestCase):
    def test_list_returns_all_channels_paginated(self):
        data = QueryExecutor.execute(filters={}, operation="list")

        self.assertEqual(data["count"], len(Channel))
        self.assertEqual(data["limit"], 20)
        self.assertEqual(data["offset"], 0)
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])
        self.assertEqual(data["results"][0]["uuid"], Channel.INSTAGRAM)
        self.assertEqual(data["results"][0]["name"], Channel.INSTAGRAM.label)

    def test_list_paginates_with_limit_and_offset(self):
        data = QueryExecutor.execute(
            filters={"limit": 2, "offset": 2}, operation="list"
        )

        self.assertEqual(data["count"], len(Channel))
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["uuid"], Channel.WHATSAPP)
        self.assertEqual(data["next"], 4)
        self.assertEqual(data["previous"], 0)

    def test_list_filters_by_search(self):
        data = QueryExecutor.execute(filters={"search": "whats"}, operation="list")

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["uuid"], Channel.WHATSAPP)

    def test_list_unwraps_querydict_lists(self):
        data = QueryExecutor.execute(
            filters={"limit": ["2"], "offset": ["0"], "search": ["email"]},
            operation="list",
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["uuid"], Channel.EMAIL)
        self.assertEqual(data["limit"], 2)
