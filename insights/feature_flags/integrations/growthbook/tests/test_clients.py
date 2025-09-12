from unittest.mock import patch, MagicMock

from django.test import TestCase

from insights.feature_flags.integrations.growthbook.clients import GrowthbookClient
from insights.sources.cache import CacheClient


class DummyCache(CacheClient):
    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value
        return True


class TestGrowthbookClient(TestCase):
    def setUp(self):
        self.cache = DummyCache()
        self.client = GrowthbookClient(
            host_base_url="https://cdn.growthbook.io",
            client_key="k",
            cache_client=self.cache,
            short_cache_key="short",
            short_cache_ttl=60,
            long_cache_key="long",
            long_cache_ttl=3600,
        )

    @patch("insights.feature_flags.integrations.growthbook.clients.requests.get")
    def test_update_definitions_sets_both_caches(self, mock_get):
        resp = MagicMock()
        resp.json.return_value = {"features": {"a": {"defaultValue": True}}}
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        data = self.client.update_feature_flags_definitions()
        self.assertIn("a", data)
        self.assertTrue(self.client.get_feature_flags_from_short_cache())
        self.assertTrue(self.client.get_feature_flags_from_long_cache())