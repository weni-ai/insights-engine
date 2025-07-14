import logging
from datetime import datetime
from uuid import UUID

from sentry_sdk import capture_exception

from insights.metrics.conversations.integrations.datalake.dataclass import (
    DatalakeConversationsTotalsMetric,
    DatalakeConversationsTotalsMetrics,
)
from insights.metrics.conversations.integrations.datalake.enums import (
    DatalakeConversationsClassification,
)
from insights.metrics.conversations.integrations.datalake.exceptions import (
    DatalakeConversationsMetricsException,
)
from insights.sources.dl_events.clients import DataLakeEventsClient


logger = logging.getLogger(__name__)


class DatalakeConversationsMetricsService:
    """
    Service for getting conversations metrics from Datalake.
    """

    def __init__(self, events_client: DataLakeEventsClient):
        self.events_client = events_client

    def get_conversations_totals(
        self,
        project_uuid: UUID,
        classification: DatalakeConversationsClassification,
        start_date: datetime,
        end_date: datetime,
    ) -> DatalakeConversationsTotalsMetrics:
        """
        Get conversations totals from Datalake.
        """

        try:
            events = self.events_client.get_events(
                project_uuid=project_uuid,
                classification=classification,
                start_date=start_date,
                end_date=end_date,
                event_name="weni_nexus_data",
            )
        except Exception as e:
            capture_exception(e)
            logger.error(e)

            raise DatalakeConversationsMetricsException(e) from e

        if not events:
            metric = DatalakeConversationsTotalsMetric(value=0, percentage=0)

            return DatalakeConversationsTotalsMetrics(
                total_conversations=metric, resolved=metric, unresolved=metric
            )

        total_conversations = 0
        resolved = 0
        unresolved = 0

        for event in events:
            total_conversations += 1
            if event.get("status") == "resolved":
                resolved += 1
            elif event.get("status") == "unresolved":
                unresolved += 1

        percentage_resolved = resolved / total_conversations
        percentage_unresolved = unresolved / total_conversations

        return DatalakeConversationsTotalsMetrics(
            total_conversations=DatalakeConversationsTotalsMetric(
                value=total_conversations, percentage=percentage_resolved
            ),
            resolved=DatalakeConversationsTotalsMetric(
                value=resolved, percentage=percentage_resolved
            ),
            unresolved=DatalakeConversationsTotalsMetric(
                value=unresolved, percentage=percentage_unresolved
            ),
        )
