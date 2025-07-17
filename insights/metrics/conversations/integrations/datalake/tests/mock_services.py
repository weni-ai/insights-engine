from datetime import datetime
from uuid import UUID
import uuid
from insights.metrics.conversations.dataclass import (
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
