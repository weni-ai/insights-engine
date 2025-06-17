from dataclasses import dataclass


@dataclass(frozen=True)
class SubjectItem:
    """
    A subject.
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class SubjectGroup:
    """
    A group of subjects.
    """

    name: str
    percentage: float
    subjects: list[SubjectItem]


@dataclass(frozen=True)
class SubjectsDistributionMetrics:
    """
    Metrics for the distribution of subjects in a conversation.
    """

    groups: list[SubjectGroup]
