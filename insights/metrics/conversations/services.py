from typing import TYPE_CHECKING
from datetime import datetime

from insights.metrics.conversations.dataclass import (
    ConversationTotalsMetrics,
    ConversationsTimeseriesMetrics,
    RoomsByQueueMetric,
    SubjectMetricData,
    SubjectsMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
)
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)

if TYPE_CHECKING:
    from uuid import UUID
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_totals(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> ConversationTotalsMetrics:
        """
        Get conversations metrics totals
        """
        # Mock data for now

        return ConversationTotalsMetrics.from_values(
            by_ai=CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"],
            by_human=CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )

    def get_timeseries(
        cls,
        project: "Project",
        start_date: datetime,
        end_date: datetime,
        unit: ConversationsTimeseriesUnit,
    ) -> ConversationsTimeseriesMetrics:
        # Mock data for now
        return ConversationsTimeseriesMetrics(
            unit=unit,
            total=CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[unit]["total"],
            by_human=CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[unit]["by_human"],
        )

    def get_subjects_metrics(
        self,
        project_uuid: str,
        start_date: datetime,
        end_date: datetime,
        conversation_type: ConversationsSubjectsType,
        limit: int | None = None,
    ) -> SubjectsMetrics:
        """
        Get subjects metrics
        """
        # Mock data for now
        subjects = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])
        total_mock_subjects_qty = len(subjects)

        if limit is None:
            limit = total_mock_subjects_qty
            has_more = False
        else:
            has_more = limit < total_mock_subjects_qty

        subjects_to_show = [
            SubjectMetricData(
                name=subject.get("name"),
                percentage=subject.get("percentage"),
            )
            for subject in subjects[:limit]
        ]

        return SubjectsMetrics(
            has_more=has_more,
            subjects=subjects_to_show,
        )

    @classmethod
    def get_rooms_numbers_by_queue(
        cls,
        project_uuid: "UUID",
        start_date: "datetime",
        end_date: "datetime",
        limit: int | None = None,
    ):
        """
        Get the rooms numbers by queue.
        """
        queues = list(
            ChatsClient().get_rooms_numbers_by_queue(project_uuid, start_date, end_date)
        )
        qty = len(queues)
        has_more = False

        if limit and qty > limit:
            queues = queues[:limit]
            has_more = True

        return RoomsByQueueMetric.from_values(queues, has_more=has_more)
