from abc import ABC, abstractmethod
from dataclasses import asdict
import json
import logging
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.utils.translation import override, gettext
from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.dataclass import (
    SalesFunnelData,
)
from insights.metrics.conversations.integrations.datalake.serializers import (
    TopicsBaseStructureSerializer,
    TopicsDistributionSerializer,
    TopicsRelationsSerializer,
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
        current_topics_data: dict,
        output_language: str = "en",
    ) -> TopicsDistributionMetrics:
        pass

    @abstractmethod
    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

    @abstractmethod
    def get_generic_metrics_by_key(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get generic metrics grouped by value from Datalake.
        """

    @abstractmethod
    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelData:
        """
        Get sales funnel data from Datalake.
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
                if not isinstance(cached_data, dict):
                    cached_data = json.loads(cached_data)

                return cached_data
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
            data_type="csat_metrics",
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        if self.cache_results and (
            cached_results := self._get_cached_results(cache_key)
        ):
            if not isinstance(cached_results, dict):
                cached_results = json.loads(cached_results)

            return cached_results

        try:
            csat_metrics = self.events_client.get_events_count_by_group(
                key="weni_csat",
                event_name=self.event_name,
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                metadata_key="agent_uuid",
                metadata_value=agent_uuid,
                table="weni_csat",
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
            payload_value = metric.get("payload_value")

            if payload_value is None:
                continue

            if isinstance(payload_value, int):
                payload_value = str(payload_value)

            payload_value = payload_value.strip('"')

            if payload_value not in scores:
                # We ignore metrics that are not CSAT scores
                # This is a safety measure to avoid unexpected values
                continue

            scores[payload_value] += metric.get("count")

        if self.cache_results:
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
        cache_key = self._get_cache_key(
            data_type="nps_metrics",
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        if self.cache_results:
            if cached_results := self._get_cached_results(cache_key):
                if not isinstance(cached_results, dict):
                    cached_results = json.loads(cached_results)

                return cached_results

        try:
            nps_metrics = self.events_client.get_events_count_by_group(
                key="weni_nps",
                event_name=self.event_name,
                project=project_uuid,
                agent_uuid=agent_uuid,
                date_start=start_date,
                date_end=end_date,
                metadata_key="agent_uuid",
                metadata_value=agent_uuid,
                table="weni_nps",
            )
        except Exception as e:
            logger.error("Failed to get nps metrics: %s", e)
            capture_exception(e)

            raise e

        scores = {str(n): 0 for n in range(0, 11)}

        for metric in nps_metrics:
            payload_value = metric.get("payload_value")

            if payload_value is None:
                continue

            if isinstance(payload_value, int):
                payload_value = str(payload_value)

            payload_value = payload_value.strip('"')

            if payload_value not in scores:
                continue

            scores[payload_value] += metric.get("count")

        if self.cache_results:
            self._save_results_to_cache(cache_key, scores)

        return scores

    def _get_unclassified_label(self, output_language: str) -> str:
        """
        Get unclassified label with the correct language translation.
        """
        with override(output_language):
            # DO NOT change gettext to gettext_lazy
            # because we need the translation to be applied
            # immediately inside this block
            return gettext("Unclassified")

    def _get_topics_events_from_datalake(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> list[dict]:
        """
        Get topics events from Datalake.
        """
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
                table="topics",
            )
        except Exception as e:
            logger.error("Failed to get topics events from Datalake: %s", e)
            capture_exception(e)

            raise e

        return topics_events

    def _get_subtopics_events_from_datalake(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> list[dict]:
        """
        Get subtopics events from Datalake.
        """
        try:
            human_support = (
                "true" if conversation_type == ConversationType.HUMAN else "false"
            )

            subtopics_events = self.events_client.get_events_count_by_group(
                event_name=self.event_name,
                project=project_uuid,
                date_start=str(start_date),
                date_end=str(end_date),
                key="topics",
                metadata_key="human_support",
                metadata_value=human_support,
                group_by="subtopic_uuid",
                table="topics",
            )
        except Exception as e:
            logger.error("Failed to get subtopics events from Datalake: %s", e)
            capture_exception(e)

            raise e

        return subtopics_events

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        current_topics_data: dict,
        output_language: str = "en",
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
            output_language=output_language,
        )

        if cached_results := self._get_cached_results(cache_key):
            if not isinstance(cached_results, dict):
                cached_results = json.loads(cached_results)

            return cached_results

        topics_events = self._get_topics_events_from_datalake(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=conversation_type,
        )
        subtopics_events = self._get_subtopics_events_from_datalake(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=conversation_type,
        )

        unclassified_label = self._get_unclassified_label(output_language)

        topics_from_subtopics = TopicsRelationsSerializer(current_topics_data).data
        topics_data = TopicsBaseStructureSerializer(
            topics_from_subtopics, unclassified_label
        ).data

        if topics_events == [{}]:
            topics_data = {}

        else:
            topics_data = TopicsDistributionSerializer(
                topics_from_subtopics, topics_data, topics_events, subtopics_events
            ).data

        if self.cache_results:
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
                    # Reconstruct ConversationsTotalsMetrics from cached data
                    return ConversationsTotalsMetrics(
                        total_conversations=ConversationsTotalsMetric(
                            value=cached_results["total_conversations"]["value"],
                            percentage=cached_results["total_conversations"][
                                "percentage"
                            ],
                        ),
                        resolved=ConversationsTotalsMetric(
                            value=cached_results["resolved"]["value"],
                            percentage=cached_results["resolved"]["percentage"],
                        ),
                        unresolved=ConversationsTotalsMetric(
                            value=cached_results["unresolved"]["value"],
                            percentage=cached_results["unresolved"]["percentage"],
                        ),
                        transferred_to_human=ConversationsTotalsMetric(
                            value=cached_results["transferred_to_human"]["value"],
                            percentage=cached_results["transferred_to_human"][
                                "percentage"
                            ],
                        ),
                    )
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
                table="conversation_classification",
            )[0].get("count", 0)
            unresolved_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                value="unresolved",
                table="conversation_classification",
            )[0].get("count", 0)
            transferred_to_human_events_count = self.events_client.get_events_count(
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                event_name=self.event_name,
                key="conversation_classification",
                metadata_key="human_support",
                metadata_value="true",
                table="conversation_classification",
            )[0].get("count", 0)
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise e

        total_conversations = (
            resolved_events_count
            + unresolved_events_count
            + transferred_to_human_events_count
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
            transferred_to_human=ConversationsTotalsMetric(
                value=transferred_to_human_events_count,
                percentage=percentage_transferred_to_human,
            ),
        )

        if self.cache_results:
            # Convert ConversationsTotalsMetrics to dict for proper JSON serialization
            results_dict = asdict(results)
            self._save_results_to_cache(
                key=cache_key,
                value=results_dict,
            )

        return results

    def get_generic_metrics_by_key(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
        key: str,
    ) -> dict:
        """
        Get generic metrics grouped by value from Datalake.
        """
        cache_key = self._get_cache_key(
            data_type="get_generic_metrics_by_key",
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
            key=key,
        )

        if self.cache_results:
            if cached_results := self._get_cached_results(cache_key):
                if not isinstance(cached_results, dict):
                    cached_results = json.loads(cached_results)

                return cached_results

        try:
            events = self.events_client.get_events_count_by_group(
                key=key,
                event_name=self.event_name,
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                metadata_key="agent_uuid",
                metadata_value=agent_uuid,
            )
        except Exception as e:
            logger.error("Failed to get generic metrics by key: %s", e)
            capture_exception(e)

            raise e

        values = {}

        for count in events:
            payload_value = count.get("payload_value")

            if payload_value is None:
                continue

            if isinstance(payload_value, int):
                payload_value = str(payload_value)

            payload_value = payload_value.strip('"')

            if payload_value in values:
                values[payload_value] += count.get("count", 0)
            else:
                values[payload_value] = count.get("count", 0)

        if self.cache_results:
            self._save_results_to_cache(cache_key, values)

        return values

    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelData:
        """
        Get sales funnel data from Datalake.
        """
        cache_key = self._get_cache_key(
            data_type="sales_funnel_data",
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        if self.cache_results and (
            cached_results := self._get_cached_results(cache_key)
        ):
            return SalesFunnelData(
                leads_count=cached_results["leads_count"],
                total_orders_count=cached_results["total_orders_count"],
                total_orders_value=cached_results["total_orders_value"],
                currency_code=cached_results["currency_code"],
            )

        # Leads events
        leads_count = self.events_client.get_events_count(
            event_name="conversion_lead",
            project=project_uuid,
            date_start=start_date,
            date_end=end_date,
        )[0].get("count", 0)

        max_pages = settings.SALES_FUNNEL_EVENTS_MAX_PAGES
        page_size = settings.SALES_FUNNEL_EVENTS_PAGE_SIZE
        page = 1

        currency_code = None

        total_orders_count = 0
        total_orders_value = 0

        while page <= max_pages:
            events = self.events_client.get_events(
                event_name="conversion_purchase",
                project=project_uuid,
                date_start=start_date,
                date_end=end_date,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

            length = len(events)

            if length == 0:
                break

            total_orders_count += length

            for event in events:
                metadata = event.get("metadata")

                if not metadata:
                    continue

                if not isinstance(metadata, dict):
                    try:
                        metadata = json.loads(metadata)
                    except Exception as e:
                        logger.error(
                            "Error on converting metadata to dict: %s" % metadata
                        )
                        raise e

                if not currency_code:
                    currency_code = metadata.get("currency")

                try:
                    value = metadata.get("value", 0)

                    if not isinstance(value, float):
                        try:
                            value = float(value)
                        except Exception as e:
                            logger.error("Error on converting value to float: %s" % e)
                            raise e

                    order_value = int(value * 100)  # convert to cents
                except Exception as e:
                    logger.error("Error on converting value to int: %s" % e)
                    capture_exception(e)
                    order_value = 0

                total_orders_value += order_value

            if page >= max_pages:
                raise ValueError("Max pages reached")

            page += 1

        if self.cache_results:
            self._save_results_to_cache(
                cache_key,
                {
                    "leads_count": leads_count,
                    "total_orders_count": total_orders_count,
                    "total_orders_value": total_orders_value,
                    "currency_code": currency_code,
                },
            )

        return SalesFunnelData(
            leads_count=leads_count,
            total_orders_count=total_orders_count,
            total_orders_value=total_orders_value,
            currency_code=currency_code,
        )
