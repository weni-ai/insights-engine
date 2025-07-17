from datetime import datetime
from typing import TYPE_CHECKING

from insights.metrics.conversations.dataclass import (
    SubjectGroup,
    SubjectItem,
    TopicsDistributionMetrics,
)
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_SUBJECTS_DISTRIBUTION_MOCK_DATA,
)


if TYPE_CHECKING:
    from insights.projects.models import Project


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    @classmethod
    def get_topics_distribution(
        cls, project: "Project", start_date: datetime, end_date: datetime
    ) -> TopicsDistributionMetrics:
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
        return TopicsDistributionMetrics(groups=groups)
