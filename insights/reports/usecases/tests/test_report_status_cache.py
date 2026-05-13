from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from insights.reports.usecases.report_status_cache import (
    ReportStatusCacheUseCase,
    SENTINEL_NO_REPORT,
)


class TestReportStatusCacheUseCaseGetCacheKey(TestCase):
    def test_get_cache_key_formats_project_uuid(self):
        project_uuid = "abc-123"
        key = ReportStatusCacheUseCase.get_cache_key(project_uuid)
        self.assertIn(project_uuid, key)

    @override_settings(
        CONVERSATIONS_REPORT_STATUS_CACHE_KEY="custom_prefix:{project_uuid}"
    )
    def test_get_cache_key_uses_setting(self):
        key = ReportStatusCacheUseCase.get_cache_key("my-uuid")
        self.assertEqual(key, "custom_prefix:my-uuid")


class TestReportStatusCacheUseCaseGet(TestCase):
    def setUp(self):
        self.project_uuid = "test-project-uuid"
        self.cache_key = ReportStatusCacheUseCase.get_cache_key(self.project_uuid)

    def tearDown(self):
        cache.delete(self.cache_key)

    def test_get_returns_miss_when_cache_is_empty(self):
        cache.delete(self.cache_key)
        result, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertIsNone(result)
        self.assertFalse(cache_hit)

    def test_get_returns_none_and_hit_for_sentinel(self):
        cache.set(self.cache_key, SENTINEL_NO_REPORT)
        result, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertIsNone(result)
        self.assertTrue(cache_hit)

    def test_get_returns_cached_value_and_hit(self):
        cached_value = {"some": "data"}
        cache.set(self.cache_key, cached_value)
        result, cache_hit = ReportStatusCacheUseCase.get(self.project_uuid)
        self.assertEqual(result, cached_value)
        self.assertTrue(cache_hit)


class TestReportStatusCacheUseCaseSet(TestCase):
    def setUp(self):
        self.project_uuid = "test-project-uuid"
        self.cache_key = ReportStatusCacheUseCase.get_cache_key(self.project_uuid)

    def tearDown(self):
        cache.delete(self.cache_key)

    def test_set_stores_value_in_cache(self):
        value = {"status": "PENDING"}
        ReportStatusCacheUseCase.set(self.project_uuid, value)
        self.assertEqual(cache.get(self.cache_key), value)

    def test_set_stores_sentinel_for_none(self):
        ReportStatusCacheUseCase.set(self.project_uuid, None)
        self.assertEqual(cache.get(self.cache_key), SENTINEL_NO_REPORT)

    @override_settings(CONVERSATIONS_REPORT_STATUS_CACHE_TTL=42)
    def test_set_uses_ttl_from_settings(self):
        with patch.object(cache, "set", wraps=cache.set) as mock_set:
            ReportStatusCacheUseCase.set(self.project_uuid, None)
            mock_set.assert_called_once_with(self.cache_key, SENTINEL_NO_REPORT, 42)


class TestReportStatusCacheUseCaseInvalidate(TestCase):
    def test_invalidate_deletes_cache_entry(self):
        project_uuid = "test-project-uuid"
        cache_key = ReportStatusCacheUseCase.get_cache_key(project_uuid)
        cache.set(cache_key, "some-value")

        ReportStatusCacheUseCase.invalidate(project_uuid)

        self.assertIsNone(cache.get(cache_key))

    def test_invalidate_does_not_error_on_missing_key(self):
        ReportStatusCacheUseCase.invalidate("nonexistent-uuid")
