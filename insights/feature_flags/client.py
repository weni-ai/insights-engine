import json
import logging
from typing import Any, Dict

from growthbook import GrowthBook

from insights.sources.cache import CacheClient

logger = logging.getLogger(__name__)


class FeatureFlagClient:
    """
    Wrapper para avaliar flags usando as definições carregadas pelo GROWTHBOOK_CLIENT.
    """

    def __init__(self) -> None:
        self.cache = CacheClient()
        self.cache_ttl = 300

    def _cache_key(self) -> str:
        return "feature_flags:evaluated:last"

    def _get_definitions(self) -> Dict[str, Any]:
        try:
            from insights.feature_flags.integrations.growthbook.instance import (
                GROWTHBOOK_CLIENT,
            )

            return GROWTHBOOK_CLIENT.get_feature_flags()
        except Exception as err:
            logger.error("Error getting GrowthBook features: %s", err, exc_info=True)
            return {}

    def is_on(self, feature_key: str, attributes: Dict[str, Any]) -> bool:
        try:
            features = self._get_definitions()
            gb = GrowthBook(attributes=attributes, features=features)
            on = bool(gb.is_on(feature_key))
            # best effort: salva último resultado para troubleshooting
            try:
                self.cache.set(
                    self._cache_key(),
                    json.dumps({"feature": feature_key, "on": on}),
                    ex=self.cache_ttl,
                )
            except Exception:
                pass
            return on
        except Exception as err:
            logger.error("Error evaluating feature flag: %s", err, exc_info=True)
            return False
