from datetime import datetime
from uuid import UUID
import uuid

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    Subtopic,
    Topic,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)


class MockConversationsMetricsService(BaseConversationsMetricsService):
    """
    Mock service for conversations metrics.
    """

    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            abandoned=ConversationsTotalsMetric(value=0, percentage=0),
        )

    def get_topics_distribution(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> TopicsDistributionMetrics:
        return TopicsDistributionMetrics(
            topics=[
                Topic(
                    uuid=uuid.uuid4(),
                    name="Topic 1",
                    percentage=100,
                    subtopics=[
                        Subtopic(
                            uuid=uuid.uuid4(),
                            name="Subtopic 1",
                            percentage=100,
                        )
                    ],
                )
            ]
        )
