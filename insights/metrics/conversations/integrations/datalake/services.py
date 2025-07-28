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
    def get_csat_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_nps_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> TopicsDistributionMetrics:
        pass

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

    def _get_cache_key(self, data_type: str, **params) -> str:
        """
        Get cache key for conversations totals with consistent datetime formatting.
        """
        formatted_params = {}
        for key, value in params.items():
            if isinstance(value, datetime):
                formatted_params[key] = value.isoformat()
            else:
                formatted_params[key] = str(value)
        return f"{data_type}_{json.dumps(formatted_params, sort_keys=True)}"

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

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        cache_key = self._get_cache_key(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        if cached_results := self._get_cached_results(cache_key):
            if not isinstance(cached_results, dict):
                cached_results = json.loads(cached_results)

            return cached_results

        try:
            csat_metrics = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                agent_uuid=agent_uuid,
                date_start=start_date,
                date_end=end_date,
            )
        except Exception as e:
            logger.error("Failed to get csat metrics: %s", e)
            capture_exception(e)

            raise e

        # The frontend application will display fixed labels for the CSAT scores
        # For example, "1" can be displayed as "Very dissatisfied"
        scores = {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0,
        }

        # Each metric is a dict grouped by the event's value
        # (in this case, the event's value is the CSAT score)
        for metric in csat_metrics:
            if metric.get("group_value") not in scores:
                # We ignore metrics that are not CSAT scores
                # This is a safety measure to avoid unexpected values
                continue

            scores[metric.get("group_value")] += metric.get("count")

        self._save_results_to_cache(cache_key, scores)

        return scores

    def get_nps_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get nps metrics from Datalake.
        """
        pass

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
            data_type="topics_distribution",
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
                "true" if conversation_type == ConversationType.HUMAN else "false"
            )

            topics_events = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                date_start=str(start_date),
                date_end=str(end_date),
                key="topics",
                metadata_key="human_support",
                metadata_value=human_support,
                group_by="topic_uuid",
            )

            # Subtopics
            subtopics_events = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                date_start=str(start_date),
                date_end=str(end_date),
                key="topics",
                metadata_key="human_support",
                metadata_value=human_support,
                group_by="subtopic_uuid",
            )
        except Exception as e:
            logger.error("Failed to get topics distribution from Datalake: %s", e)
            capture_exception(e)

            raise e

        topics_data = {
            "OTHER": {"name": "Other", "uuid": None, "count": 0, "subtopics": {}}
        }

        topics_from_subtopics = {
            subtopic.topic_uuid: {
                "name": subtopic.topic_name,
                "uuid": subtopic.topic_uuid,
                "subtopics": {
                    subtopic.subtopic_uuid: {
                        "name": subtopic.subtopic_name,
                        "uuid": subtopic.subtopic_uuid,
                    }
                    for subtopic in subtopics
                },
            }
            for subtopic in subtopics
        }

        for topic_uuid, topic_data in topics_from_subtopics.items():
            if topic_uuid not in topics_data:
                topic_subtopics = {}
                for subtopic_uuid, subtopic_data in topic_data.get(
                    "subtopics", {}
                ).items():
                    topic_subtopics[subtopic_uuid] = {
                        "name": subtopic_data.get("name"),
                        "uuid": subtopic_uuid,
                    }

                topic_subtopics["OTHER"] = {
                    "count": 0,
                    "name": "Other",
                    "uuid": None,
                }

                topics_data[topic_uuid] = {
                    "name": topic_data.get("name"),
                    "uuid": topic_uuid,
                    "count": 0,
                    "subtopics": topic_subtopics,
                }
            else:
                topics_data[topic_uuid]["count"] += 0

        if topics_events == [{}]:
            return topics_data

        for topic_event in topics_events:
            topic_uuid = topic_event.get("group_value")

            if topic_uuid in {"", None} or topic_uuid not in topics_from_subtopics:
                topics_data["OTHER"]["count"] += topic_event.get("count", 0)
                continue

            topic_name = topic_event.get("topic_name")
            topic_count = topic_event.get("count", 0)

            topics_data[topic_uuid]["count"] += topic_count

        if subtopics_events == [{}]:
            return subtopics_events

        subtopics = {str(subtopic.subtopic_uuid): subtopic for subtopic in subtopics}

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
                    "name": topic_name,
                    "uuid": topic_uuid,
                    "count": 0,
                    "subtopics": {},
                }

            topics_data[topic_uuid]["count"] += subtopic_event.get("count", 0)

            subtopic_name = subtopics[subtopic_uuid].subtopic_name

            if subtopic_uuid not in topics_data[topic_uuid]["subtopics"]:
                topics_data[topic_uuid]["subtopics"][subtopic_uuid] = {
                    "count": 0,
                    "name": subtopic_name,
                    "uuid": subtopic_uuid,
                }

            topics_data[topic_uuid]["subtopics"][subtopic_uuid][
                "count"
            ] += subtopic_event.get("count", 0)
            topics_data[topic_uuid]["subtopics"]["OTHER"][
                "count"
            ] -= subtopic_event.get("count", 0)

        self._save_results_to_cache(cache_key, topics_data)

        return topics_data

    def get_conversations_totals(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

        cache_key = self._get_cache_key(
            data_type="conversations_totals",
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        if self.cache_results:
            try:
                cached_results = self._get_cached_results(
                    key=cache_key,
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
                (resolved_events_count / total_conversations * 100)
                if total_conversations > 0
                else 0
            ),
            2,
        )

        percentage_unresolved = round(
            (
                (unresolved_events_count / total_conversations * 100)
                if total_conversations > 0
                else 0
            ),
            2,
        )

        percentage_abandoned = round(
            (
                (abandoned_events_count / total_conversations * 100)
                if total_conversations > 0
                else 0
            ),
            2,
        )

        percentage_transferred_to_human = round(
            (
                (transferred_to_human_events_count / total_conversations * 100)
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
            self._save_results_to_cache(
                key=cache_key,
                value=results,
            )

        return results
