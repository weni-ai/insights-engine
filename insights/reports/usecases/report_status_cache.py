from typing import Optional, Tuple

from django.conf import settings
from django.core.cache import cache

from insights.reports.models import Report


SENTINEL_NO_REPORT = "NO_REPORT"


class ReportStatusCacheUseCase:
    @staticmethod
    def get_cache_key(project_uuid: str) -> str:
        return settings.CONVERSATIONS_REPORT_STATUS_CACHE_KEY.format(
            project_uuid=project_uuid
        )

    @classmethod
    def get(cls, project_uuid: str) -> Tuple[Optional[Report], bool]:
        """Returns (report_or_none, cache_hit)."""
        cached = cache.get(cls.get_cache_key(project_uuid))
        if cached is None:
            return None, False
        if cached == SENTINEL_NO_REPORT:
            return None, True
        return cached, True

    @classmethod
    def set(cls, project_uuid: str, report: Optional[Report]) -> None:
        cache.set(
            cls.get_cache_key(project_uuid),
            report if report is not None else SENTINEL_NO_REPORT,
            settings.CONVERSATIONS_REPORT_STATUS_CACHE_TTL,
        )

    @classmethod
    def invalidate(cls, project_uuid: str) -> None:
        cache.delete(cls.get_cache_key(project_uuid))
