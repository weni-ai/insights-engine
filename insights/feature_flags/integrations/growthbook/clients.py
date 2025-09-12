import json
import logging
import requests
from typing import Optional

from django.conf import settings
from sentry_sdk import capture_exception

from insights.sources.cache import CacheClient

logger = logging.getLogger(__name__)

class BaseGrowthbookClient:
    def get_feature_flags_from_short_cache(self) -> dict:
        raise NotImplementedError

    def get_feature_flags_from_long_cache(self) -> dict:
        raise NotImplementedError

    def get_feature_flags_from_cache(self) -> Optional[dict]:
        short = self.get_feature_flags_from_short_cache()
        if short:
            return short
        return self.get_feature_flags_from_long_cache() or None

    def set_feature_flags_to_short_cache(self, feature_flags: dict) -> None:
        raise NotImplementedError

    def set_feature_flags_to_long_cache(self, feature_flags: dict) -> None:
        raise NotImplementedError

    def set_feature_flags_to_cache(self, feature_flags: dict) -> None:
        self.set_feature_flags_to_short_cache(feature_flags)
        self.set_feature_flags_to_long_cache(feature_flags)

    def update_feature_flags_definitions(self) -> dict:
        raise NotImplementedError

    def get_feature_flags(self) -> dict:
        cached = self.get_feature_flags_from_cache()
        if cached is not None:
            return cached
        return self.update_feature_flags_definitions()

class GrowthbookClient(BaseGrowthbookClient):
    def __init__(
        self,
        host_base_url: str,
        client_key: str,
        cache_client: CacheClient,
        short_cache_key: str,
        short_cache_ttl: int,
        long_cache_key: str,
        long_cache_ttl: int,
    ) -> None:
        self.host_base_url = host_base_url.rstrip("/")
        self.client_key = client_key
        self.cache_client = cache_client
        self.short_cache_key = short_cache_key
        self.short_cache_ttl = short_cache_ttl
        self.long_cache_key = long_cache_key
        self.long_cache_ttl = long_cache_ttl

    def get_feature_flags_from_short_cache(self) -> dict:
        cached = self.cache_client.get(self.short_cache_key)
        try:
            return json.loads(cached) if cached else {}
        except Exception:
            logger.warning("Invalid short cache; ignoring")
            return {}

    def get_feature_flags_from_long_cache(self) -> dict:
        cached = self.cache_client.get(self.long_cache_key)
        try:
            return json.loads(cached) if cached else {}
        except Exception:
            logger.warning("Invalid long cache; ignoring")
            return {}

    def set_feature_flags_to_short_cache(self, feature_flags: dict) -> None:
        self.cache_client.set(
            self.short_cache_key,
            json.dumps(feature_flags, ensure_ascii=False),
            self.short_cache_ttl,
        )

    def set_feature_flags_to_long_cache(self, feature_flags: dict) -> None:
        self.cache_client.set(
            self.long_cache_key,
            json.dumps(feature_flags, ensure_ascii=False),
            self.long_cache_ttl,
        )

    def update_feature_flags_definitions(self) -> dict:
        try:
            response = requests.get(
                f"{self.host_base_url}/api/features/{self.client_key}",
                timeout=60,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("Failed to update GrowthBook features: %s", e, exc_info=True)
            capture_exception(e)
            raise

        payload = response.json() or {}
        features = payload.get("features", {}) or {}
        self.set_feature_flags_to_cache(features)

        return features
