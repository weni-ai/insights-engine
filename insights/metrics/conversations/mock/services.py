from uuid import UUID
from datetime import datetime

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    SubtopicMetrics,
    TopicMetrics,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.enums import (
    AvailableWidgetsListType,
    ConversationType,
    TopicsDistributionMetrics,
    SalesFunnelMetrics,
    AvailableWidgetsList,
)
from insights.widgets.models import Widget
from insights.metrics.conversations.services import BaseConversationsMetricsService


class MockConversationsMetricsService(BaseConversationsMetricsService):
    def get_topics(self, project_uuid: UUID) -> dict:
        return {}

    def get_subtopics(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        return {}

    def create_topic(self, project_uuid: UUID, name: str, description: str) -> dict:
        return {}

    def create_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, name: str, description: str
    ) -> dict:
        return {}

    def delete_topic(self, project_uuid: UUID, topic_uuid: UUID) -> dict:
        return {}

    def delete_subtopic(
        self, project_uuid: UUID, topic_uuid: UUID, subtopic_uuid: UUID
    ) -> dict:
        return {}

    def get_topics_distribution(
        self,
        project_uuid: UUID,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationType,
        output_language: str = "en",
    ) -> TopicsDistributionMetrics:
        return TopicsDistributionMetrics(
            topics=[
                TopicMetrics(
                    uuid=UUID.uuid4(),
                    name="Topic 1",
                    quantity=120,
                    percentage=24.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 1.1",
                            quantity=50,
                            percentage=41.67,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 1.2",
                            quantity=40,
                            percentage=33.33,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 1.3",
                            quantity=30,
                            percentage=25.0,
                        ),
                    ],
                ),
                TopicMetrics(
                    uuid=UUID.uuid4(),
                    name="Topic 2",
                    quantity=100,
                    percentage=20.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 2.1",
                            quantity=45,
                            percentage=45.0,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 2.2",
                            quantity=35,
                            percentage=35.0,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 2.3",
                            quantity=20,
                            percentage=20.0,
                        ),
                    ],
                ),
                TopicMetrics(
                    uuid=UUID.uuid4(),
                    name="Topic 3",
                    quantity=90,
                    percentage=18.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 3.1",
                            quantity=40,
                            percentage=44.44,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 3.2",
                            quantity=30,
                            percentage=33.33,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 3.3",
                            quantity=20,
                            percentage=22.22,
                        ),
                    ],
                ),
                TopicMetrics(
                    uuid=UUID.uuid4(),
                    name="Topic 4",
                    quantity=110,
                    percentage=22.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 4.1",
                            quantity=55,
                            percentage=50.0,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 4.2",
                            quantity=33,
                            percentage=30.0,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 4.3",
                            quantity=22,
                            percentage=20.0,
                        ),
                    ],
                ),
                TopicMetrics(
                    uuid=UUID.uuid4(),
                    name="Topic 5",
                    quantity=80,
                    percentage=16.0,
                    subtopics=[
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 5.1",
                            quantity=35,
                            percentage=43.75,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 5.2",
                            quantity=28,
                            percentage=35.0,
                        ),
                        SubtopicMetrics(
                            uuid=UUID.uuid4(),
                            name="Subtopic 5.3",
                            quantity=17,
                            percentage=21.25,
                        ),
                    ],
                ),
            ]
        )

    def get_totals(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> ConversationsTotalsMetrics:
        return ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
        )

    def get_sales_funnel_data(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> SalesFunnelMetrics:
        return {}

    def check_if_sales_funnel_data_exists(self, project_uuid: UUID) -> bool:
        return False

    def get_available_widgets(
        self, project_uuid: UUID, widget_type: AvailableWidgetsListType | None = None
    ) -> AvailableWidgetsList:
        return []

    def get_crosstab_data(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        return {}
