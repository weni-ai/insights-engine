from typing import TYPE_CHECKING
from datetime import datetime

from insights.metrics.conversations.dataclass import (
    ConversationTotalsMetrics,
    ConversationsTimeseriesMetrics,
    SubjectMetricData,
    SubjectsMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
)
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)

if TYPE_CHECKING:
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
