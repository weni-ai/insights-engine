from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from uuid import UUID

from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    Subtopic,
    Topic,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType
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
    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> TopicsDistributionMetrics:
        pass


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

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> TopicsDistributionMetrics:
        """
        Get topics distribution from Datalake.
        """
        # TODO: Add cache
        # TODO: Filter by conversation type (metadata)

        try:
            events = self.events_client.get_events(
                project_uuid=project_uuid,
                start_date=start_date,
                end_date=end_date,
                key="topics",
            )
        except Exception as e:
            logger.error("Failed to get topics distribution from Datalake: %s", e)
            capture_exception(e)

            raise e

        topics_data = {"OTHER": 0}
        total_topics_count = 0

        for event in events:
            total_topics_count += 1
            metadata = event.get("metadata")

            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            topic_uuid = metadata.get("topic_uuid")
            topic_name = metadata.get("value")

            if not topic_uuid:
                topics_data["OTHER"] += 1
                continue

            if topic_uuid not in topics_data:
                topics_data[topic_uuid] = {"subtopics": {}, "count": 0}

            subtopic_uuid = metadata.get("subtopic_uuid")
            subtopic_name = metadata.get("subtopic")

            if subtopic_uuid:
                topics_data[topic_uuid]["count"] += 1
                if subtopic_uuid not in topics_data[topic_uuid]["subtopics"]:
                    topics_data[topic_uuid]["subtopics"][subtopic_uuid] = 0

                topics_data[topic_uuid]["subtopics"][subtopic_uuid] += 1

        topics = []

        for topic_uuid, topic_data in topics_data.items():
            topic = Topic(
                uuid=topic_uuid,
                name=topic_name,
                percentage=topic_data["count"] / total_topics_count,
                subtopics=[
                    Subtopic(
                        uuid=subtopic_uuid,
                        name=subtopic_name,
                        percentage=subtopic_data["count"] / topic_data["count"],
                    )
                    for subtopic_uuid, subtopic_data in topic_data["subtopics"].items()
                ],
            )
            topics.append(topic)

        return TopicsDistributionMetrics(topics=topics)
