from dataclasses import dataclass


@dataclass(frozen=True)
class SubjectMetricData:
    """
    Dataclass for subjects metrics by type
    """

    name: str
    percentage: float


@dataclass(frozen=True)
class SubjectsMetrics:
    """
    Dataclass for subjects metrics
    """

    has_more: bool
    subjects: list[SubjectMetricData]
