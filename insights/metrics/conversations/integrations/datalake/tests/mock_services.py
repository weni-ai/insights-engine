from datetime import datetime
from uuid import UUID
import uuid
from insights.metrics.conversations.dataclass import (
    SubtopicTopicRelation,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)


class MockDatalakeConversationsMetricsService(BaseConversationsMetricsService):
    """
    Mock service for conversations metrics.
    """

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        subtopics: list[SubtopicTopicRelation],
    ) -> TopicsDistributionMetrics:
        return {
            "OTHER": {
                "name": "OTHER",
                "uuid": None,
                "count": 100,
                "subtopics": {},
            },
            uuid.uuid4(): {
                "name": "Cancelamento",
                "uuid": "2026cedc-67f6-4a04-977a-55cc581defa9",
                "count": 100,
                "subtopics": {
                    uuid.uuid4(): {
                        "name": "Subtopic 1",
                        "uuid": uuid.uuid4(),
                        "count": 70,
                    },
                    "OTHER": {
                        "name": "OTHER",
                        "uuid": None,
                        "count": 30,
                    },
                },
            },
        }
