from datetime import datetime
from uuid import UUID
import uuid
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
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

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        agent_uuid: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        return {
            "results": [
                {"label": "5", "value": 20.99, "full_value": 17},
                {"label": "4", "value": 16.05, "full_value": 13},
                {"label": "3", "value": 14.81, "full_value": 12},
                {"label": "2", "value": 9.88, "full_value": 8},
                {"label": "1", "value": 8.64, "full_value": 7},
            ]
        }

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

    def get_conversations_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            abandoned=ConversationsTotalsMetric(value=0, percentage=0),
            transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
        )
