from abc import ABC, abstractmethod
import logging
from datetime import datetime
from uuid import UUID

from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.sources.dl_events.clients import (
    BaseDataLakeEventsClient,
    DataLakeEventsClient,
)


logger = logging.getLogger(__name__)


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
    ):
        self.events_client = events_client
        self.event_name = "weni_nexus_data"

    def get_conversations_totals(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

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

        return ConversationsTotalsMetrics(
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
