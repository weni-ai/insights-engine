from datetime import datetime
from typing import TYPE_CHECKING

from insights.metrics.conversations.dataclass import (
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
    DatalakeConversationsMetricsService,
)


if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    def __init__(
        self,
        datalake_client: BaseConversationsMetricsService = DatalakeConversationsMetricsService(),
    ):
        self.datalake_client = datalake_client

    @classmethod
    def get_topics_distribution(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> TopicsDistributionMetrics:
        pass
