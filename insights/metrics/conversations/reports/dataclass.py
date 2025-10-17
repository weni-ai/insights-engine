from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ConversationsReportWorksheet:
    """
    Worksheet for the conversations report.
    """

    name: str
    data: list[dict]


@dataclass(frozen=True)
class ConversationsReportFile:
    """
    File for the conversations report.
    """

    name: str
    content: str


@dataclass(frozen=True)
class AvailableReportWidgets:
    sections: list[str]
    custom_widgets: list[UUID]
