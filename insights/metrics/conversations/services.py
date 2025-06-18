from typing import TYPE_CHECKING
from datetime import datetime

import pytz

from insights.metrics.conversations.dataclass import (
    QueueMetric,
    RoomsByQueueMetric,
    ConversationTotalsMetrics,
    ConversationsTimeseriesMetrics,
    SubjectGroup,
    SubjectItem,
    SubjectMetricData,
    SubjectsDistributionMetrics,
    SubjectsMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
)
from insights.metrics.conversations.integrations.chats.db.client import ChatsClient
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)

if TYPE_CHECKING:
    from datetime import date
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
        project: "Project",
        start_date: "date",
        end_date: "date",
        limit: int | None = None,
    ):
        """
        Get the rooms numbers by queue.
        """

        if project.timezone is None:
            tz = pytz.utc
        else:
            tz = pytz.timezone(project.timezone)

        # Create naive datetime at midnight in the project's timezone
        local_start = datetime.combine(start_date, datetime.min.time())
        local_end = datetime.combine(end_date, datetime.max.time())

        # Convert to UTC while preserving the intended local time
        start_datetime = tz.localize(local_start).astimezone(pytz.UTC)
        end_datetime = tz.localize(local_end).astimezone(pytz.UTC)

        queues = list(
            ChatsClient().get_rooms_numbers_by_queue(
                project.uuid,
                start_datetime,
                end_datetime,
            )
        )
        qty = len(queues)
        has_more = False

        queues_metrics = []
        total_rooms = sum(queue.rooms_number for queue in queues)

        queues_range = min(qty, limit) if limit else qty

        for queue in queues[:queues_range]:
            # Handle case where total_rooms is 0 to avoid ZeroDivisionError
            percentage = (
                0
                if total_rooms == 0
                else round(queue.rooms_number / total_rooms * 100, 2)
            )
            queues_metrics.append(
                QueueMetric(
                    name=queue.queue_name,
                    percentage=percentage,
                )
            )

        if limit and qty > limit:
            has_more = True

        return RoomsByQueueMetric(queues=queues_metrics, has_more=has_more)

    @classmethod
    def get_subjects_distribution(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> SubjectsDistributionMetrics:
        # Mock data for now
        groups = []
        for group in CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA["groups"]:
            subjects = []
            for subject in group["subjects"]:
                subjects.append(
                    SubjectItem(name=subject["name"], percentage=subject["percentage"])
                )
            groups.append(
                SubjectGroup(
                    name=group["name"],
                    percentage=group["percentage"],
                    subjects=subjects,
                )
            )
        return SubjectsDistributionMetrics(groups=groups)
