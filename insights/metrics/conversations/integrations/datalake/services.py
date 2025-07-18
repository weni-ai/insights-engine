from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from uuid import UUID
from dataclasses import asdict


from django.conf import settings
from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    SubtopicMetrics,
    TopicMetrics,
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
    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

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

    def _get_conversations_totals_cached_results(
        self, key: str
    ) -> ConversationsTotalsMetrics:
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
                cached_results = self._get_conversations_totals_cached_results(
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
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise e

        total_conversations = (
            resolved_events_count + unresolved_events_count + abandoned_events_count
        )

        percentage_resolved = (
            100 * resolved_events_count / total_conversations
            if total_conversations > 0
            else 0
        )
        percentage_unresolved = (
            100 * unresolved_events_count / total_conversations
            if total_conversations > 0
            else 0
        )
        percentage_abandoned = (
            100 * abandoned_events_count / total_conversations
            if total_conversations > 0
            else 0
        )

        # Round percentages to 2 decimal places
        percentage_resolved = (
            round(percentage_resolved, 2) if percentage_resolved > 0 else 0
        )
        percentage_unresolved = (
            round(percentage_unresolved, 2) if percentage_unresolved > 0 else 0
        )
        percentage_abandoned = (
            round(percentage_abandoned, 2) if percentage_abandoned > 0 else 0
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

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> TopicsDistributionMetrics:
        cache_key = self._get_cache_key(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=conversation_type,
        )

        if cached_results := self._get_cached_results(cache_key):
            cached_results = json.loads(cached_results)
            topics = [
                TopicMetrics(
                    uuid=topic["uuid"],
                    name=topic["name"],
                    percentage=topic["percentage"],
                    subtopics=[
                        SubtopicMetrics(
                            uuid=subtopic["uuid"],
                            name=subtopic["name"],
                            percentage=subtopic["percentage"],
                        )
                        for subtopic in topic["subtopics"]
                    ],
                )
                for topic in cached_results["topics"]
            ]

            return TopicsDistributionMetrics(topics=topics)

        try:
            human_support = (
                True if conversation_type == ConversationType.HUMAN else False
            )

            events = self.events_client.get_events(
                project=project_uuid,
                start_date=start_date,
                end_date=end_date,
                key="topics",
                human_support=human_support,
            )
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise e

        topics_data = {}
        total_topics_count = 0

        other_count = 0

        for event in events:
            total_topics_count += 1
            metadata = event.get("metadata")

            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            topic_uuid = metadata.get("topic_uuid")
            topic_name = metadata.get("value")

            if not topic_uuid:
                other_count += 1
                continue

            if topic_uuid not in topics_data:
                topics_data[topic_uuid] = {
                    "subtopics": {},
                    "count": 0,
                    "other_count": 0,
                }

            subtopic_uuid = metadata.get("subtopic_uuid")
            subtopic_name = metadata.get("subtopic")

            if subtopic_uuid:
                topics_data[topic_uuid]["count"] += 1
                if subtopic_uuid not in topics_data[topic_uuid]["subtopics"]:
                    topics_data[topic_uuid]["subtopics"][subtopic_uuid] = 0

                topics_data[topic_uuid]["subtopics"][subtopic_uuid] += 1

        topics = []

        if other_count > 0:
            topics.append(
                TopicMetrics(
                    uuid=None,
                    name="OTHER",
                    percentage=other_count / total_topics_count,
                    subtopics=[],
                )
            )

        for topic_uuid, topic_data in topics_data.items():
            topic = TopicMetrics(
                uuid=str(topic_uuid),
                name=topic_name,
                percentage=topic_data["count"] / total_topics_count,
                subtopics=[
                    SubtopicMetrics(
                        uuid=str(subtopic_uuid),
                        name=subtopic_name,
                        percentage=subtopic_data["count"] / topic_data["count"],
                    )
                    for subtopic_uuid, subtopic_data in topic_data["subtopics"].items()
                ],
            )
            topics.append(topic)

        topics_distribution = TopicsDistributionMetrics(topics=topics)

        serialized_topics_distribution = asdict(topics_distribution)
        self._save_results_to_cache(cache_key, serialized_topics_distribution)

        return topics_distribution
