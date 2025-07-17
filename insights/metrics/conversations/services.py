import logging
from datetime import datetime
from typing import TYPE_CHECKING


from sentry_sdk import capture_exception

from insights.metrics.conversations.dataclass import (
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
    DatalakeConversationsMetricsService,
)


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        datalake_service: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
    ):
        self.datalake_service = datalake_service

    def get_topics_distribution(
        self, project: "Project", start_date: datetime, end_date: datetime
    ) -> TopicsDistributionMetrics:
        try:
            topics = self.datalake_service.get_topics_distribution(
                project_uuid=project.uuid,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            logger.error("Failed to get topics distribution: %s", e)
            event_id = capture_exception(e)

            raise ConversationsMetricsError(
                f"Failed to get topics distribution. Event ID: {event_id}"
            ) from e

        return topics
