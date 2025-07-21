from datetime import datetime
from uuid import UUID
import uuid
from insights.metrics.conversations.dataclass import (
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)


class MockConversationsMetricsService(BaseConversationsMetricsService):
    """
    Mock service for conversations metrics.
    """

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
    ) -> TopicsDistributionMetrics:
        return {
            "OTHER": {
                "name": "OTHER",
                "count": 100,
                "subtopics": {},
            },
            uuid.uuid4(): {
                "name": "Topic 1",
                "count": 100,
                "subtopics": {
                    uuid.uuid4(): {"name": "Subtopic 1", "count": 100},
                },
            },
        }
