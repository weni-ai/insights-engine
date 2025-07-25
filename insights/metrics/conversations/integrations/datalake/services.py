from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from uuid import UUID


from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    SubtopicTopicRelation,
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
        subtopics: list[SubtopicTopicRelation],
    ) -> dict:
        """
        Get topics distribution from Datalake.
        """
        cache_key = self._get_cache_key(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=conversation_type,
        )

        if cached_results := self._get_cached_results(cache_key):
            if not isinstance(cached_results, dict):
                cached_results = json.loads(cached_results)

            return cached_results

        try:
            human_support = (
                True if conversation_type == ConversationType.HUMAN else False
            )

            topics_events = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                key="topics",
                metadata_key="human_support",
                metadata_value=str(human_support),
                group_by="topic_uuid",
            )

            # Subtopics
            subtopics_events = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                key="topics",
                metadata_key="human_support",
                metadata_value=str(human_support),
                group_by="subtopic_uuid",
            )
        except Exception as e:
            logger.error("Failed to get topics distribution from Datalake: %s", e)
            capture_exception(e)

            raise e

        topics_data = {"OTHER": {"topic_name": "Other", "count": 0, "subtopics": {}}}

        for topic_event in topics_events:
            if topic_event.get("group_value") in {"", None}:
                topics_data["OTHER"]["count"] += topic_event.get("count", 0)
                continue

            topic_uuid = topic_event.get("group_value")
            topic_name = topic_event.get("topic_name")
            topic_count = topic_event.get("count")

            if topic_uuid not in topics_data:
                topics_data[topic_uuid] = {
                    "topic_name": topic_name,
                    "topic_uuid": topic_uuid,
                    "count": topic_count,
                    "subtopics": {
                        "OTHER": {
                            "count": topic_count,
                            "subtopic_name": "Other",
                            "subtopic_uuid": "OTHER",
                        },
                    },
                }

        subtopics = {str(subtopic.uuid): subtopic for subtopic in subtopics}

        for subtopic_event in subtopics_events:
            subtopic_uuid = subtopic_event.get("group_value")

            if not subtopic_uuid:
                continue

            if subtopic_uuid not in subtopics:
                topics_data["OTHER"]["count"] += subtopic_event.get("count", 0)
                continue

            topic_uuid = subtopics[subtopic_uuid].topic_uuid
            topic_name = subtopics[subtopic_uuid].topic_name

            if topic_uuid not in topics_data:
                topics_data[topic_uuid] = {
                    "topic_name": topic_name,
                    "topic_uuid": topic_uuid,
                    "count": 0,
                    "subtopics": {},
                }

            topics_data[topic_uuid]["count"] += subtopic_event.get("count", 0)

            subtopic_name = subtopics[subtopic_uuid].subtopic_name

            if subtopic_uuid not in topics_data[topic_uuid]["subtopics"]:
                topics_data[topic_uuid]["subtopics"][subtopic_uuid] = {
                    "count": 0,
                    "subtopic_name": subtopic_name,
                    "subtopic_uuid": subtopic_uuid,
                }

            topics_data[topic_uuid]["subtopics"][subtopic_uuid][
                "count"
            ] += subtopic_event.get("count", 0)
            topics_data[topic_uuid]["subtopics"]["OTHER"][
                "count"
            ] -= subtopic_event.get("count", 0)

        self._save_results_to_cache(cache_key, topics_data)

        return topics_data
