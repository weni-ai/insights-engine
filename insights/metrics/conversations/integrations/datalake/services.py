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
            logger.warning("Failed to save results to cache: %s", e)

    def _get_cached_results(self, key: str) -> dict:
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
                return data
            return None
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as e:
            logger.warning("Failed to deserialize cached data: %s", e)

            return None

    def _get_conversations_totals_from_cache(
        self, key: str
    ) -> ConversationsTotalsMetrics:
        """
        Get results from cache with JSON deserialization.
        """
        cached_data = self._get_cached_results(key)
        if cached_data:
            return ConversationsTotalsMetrics(
                total_conversations=ConversationsTotalsMetric(
                    value=cached_data["total_conversations"]["value"],
                    percentage=cached_data["total_conversations"]["percentage"],
                ),
                resolved=ConversationsTotalsMetric(
                    value=cached_data["resolved"]["value"],
                    percentage=cached_data["resolved"]["percentage"],
                ),
                unresolved=ConversationsTotalsMetric(
                    value=cached_data["unresolved"]["value"],
                    percentage=cached_data["unresolved"]["percentage"],
                ),
                abandoned=ConversationsTotalsMetric(
                    value=cached_data["abandoned"]["value"],
                    percentage=cached_data["abandoned"]["percentage"],
                ),
                transferred_to_human=ConversationsTotalsMetric(
                    value=cached_data["transferred_to_human"]["value"],
                    percentage=cached_data["transferred_to_human"]["percentage"],
                ),
            )
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
                cached_results = self._get_conversations_totals_from_cache(
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
            resolved_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                value="resolved",
            )[0].get("count", 0)
            unresolved_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                value="unresolved",
            )[0].get("count", 0)
            abandoned_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                value="abandoned",
            )[0].get("count", 0)
            transferred_to_human_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                metadata_key="human_support",
                metadata_value="true",
            )[0].get("count", 0)
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise e

        total_conversations = (
            resolved_events_count + unresolved_events_count + abandoned_events_count
        )

        percentage_resolved = round(
            (
                (resolved_events_count * (total_conversations / 100))
                if total_conversations > 0
                else 0
            ),
            2,
        )

        percentage_unresolved = round(
            (
                (unresolved_events_count * (total_conversations / 100))
                if total_conversations > 0
                else 0
            ),
            2,
        )
        percentage_abandoned = round(
            (
                (abandoned_events_count * (total_conversations / 100))
                if total_conversations > 0
                else 0
            ),
            2,
        )
        percentage_transferred_to_human = round(
            (
                (transferred_to_human_events_count * (total_conversations / 100))
                if total_conversations > 0
                else 0
            ),
            2,
        )

        results = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(
                value=total_conversations, percentage=100
            ),
            resolved=ConversationsTotalsMetric(
                value=resolved_events_count, percentage=percentage_resolved
            ),
            unresolved=ConversationsTotalsMetric(
                value=unresolved_events_count, percentage=percentage_unresolved
            ),
            abandoned=ConversationsTotalsMetric(
                value=abandoned_events_count, percentage=percentage_abandoned
            ),
            transferred_to_human=ConversationsTotalsMetric(
                value=transferred_to_human_events_count,
                percentage=percentage_transferred_to_human,
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
