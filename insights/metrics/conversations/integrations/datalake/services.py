from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from uuid import UUID

from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.sources.cache import CacheClient
from insights.sources.dl_events.clients import (
    BaseDataLakeEventsClient,
    DataLakeEventsClient,
)


logger = logging.getLogger(__name__)

CACHE_RESULTS = settings.CACHE_DATALAKE_EVENTS_RESULTS
CACHE_TTL = settings.CACHE_DATALAKE_EVENTS_RESULTS_TTL


class BaseConversationsMetricsService(ABC):
    """
    Base class for conversations metrics services.
    """

    @abstractmethod
    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """


class DatalakeConversationsMetricsService(BaseConversationsMetricsService):
    """
    Service for getting conversations metrics from Datalake.
    """

    def __init__(
        self,
        events_client: BaseDataLakeEventsClient = DataLakeEventsClient(),
        cache_results: bool = CACHE_RESULTS,
        cache_client: CacheClient = CacheClient(),
        cache_ttl: int = CACHE_TTL,
    ):
        self.events_client = events_client
        self.event_name = "weni_nexus_data"
        self.cache_results = cache_results
        self.cache_client = cache_client
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, **params) -> str:
        """
        Get cache key for conversations totals with consistent datetime formatting.
        """
        formatted_params = {}
        for key, value in params.items():
            if isinstance(value, datetime):
                formatted_params[key] = value.isoformat()
            else:
                formatted_params[key] = str(value)
        return f"conversations_totals_{json.dumps(formatted_params, sort_keys=True)}"

    def _save_results_to_cache(self, key: str, value) -> None:
        """
        Cache results with JSON serialization.
        """
        try:
            serialized_value = json.dumps(value, default=str)
            self.cache_client.set(key, serialized_value, ex=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Failed to save results to cache: {e}")

    def _get_results_from_cache(self, key: str) -> ConversationsTotalsMetrics:
        """
        Get results from cache with JSON deserialization.
        """
        try:
            cached_data = self.cache_client.get(key)
            if cached_data:
                # Handle both string and bytes from Redis
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode("utf-8")

                # Parse the JSON data and reconstruct the objects
                data = json.loads(cached_data)

                # Reconstruct ConversationsTotalsMetrics from cached data
                return ConversationsTotalsMetrics(
                    total_conversations=ConversationsTotalsMetric(
                        value=data["total_conversations"]["value"],
                        percentage=data["total_conversations"]["percentage"],
                    ),
                    resolved=ConversationsTotalsMetric(
                        value=data["resolved"]["value"],
                        percentage=data["resolved"]["percentage"],
                    ),
                    unresolved=ConversationsTotalsMetric(
                        value=data["unresolved"]["value"],
                        percentage=data["unresolved"]["percentage"],
                    ),
                )
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to deserialize cached data: {e}")
        return None

    def get_conversations_totals(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

        if self.cache_results:
            try:
                cached_results = self._get_results_from_cache(
                    key=self._get_cache_key(
                        project_uuid=project_uuid,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                if cached_results:
                    return cached_results
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        try:
            events = self.events_client.get_events(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
            )
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise e

        if not events:
            metric = ConversationsTotalsMetric(value=0, percentage=0)

            return ConversationsTotalsMetrics(
                total_conversations=metric, resolved=metric, unresolved=metric
            )

        total_conversations = 0
        resolved = 0
        unresolved = 0

        for event in events:
            value = event.get("value")
            total_conversations += 1
            if value in ("resolved", '"resolved"'):
                resolved += 1
            elif value in ("unresolved", '"unresolved"'):
                unresolved += 1

        percentage_resolved = (
            100 * resolved / total_conversations if total_conversations > 0 else 0
        )
        percentage_unresolved = (
            100 * unresolved / total_conversations if total_conversations > 0 else 0
        )
        percentage_resolved = (
            round(percentage_resolved, 2) if percentage_resolved > 0 else 0
        )
        percentage_unresolved = (
            round(percentage_unresolved, 2) if percentage_unresolved > 0 else 0
        )

        results = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(
                value=total_conversations, percentage=100
            ),
            resolved=ConversationsTotalsMetric(
                value=resolved, percentage=percentage_resolved
            ),
            unresolved=ConversationsTotalsMetric(
                value=unresolved, percentage=percentage_unresolved
            ),
        )

        if self.cache_results:
            params = {
                "project_uuid": project_uuid,
                "start_date": start_date,
                "end_date": end_date,
            }
            self._save_results_to_cache(
                key=self._get_cache_key(**params), value=results
            )

        return results
