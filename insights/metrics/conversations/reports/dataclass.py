from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ConversationsReportWorksheet:
    """
    Worksheet for the conversations report.
    """

    name: str
    data: list[dict] | Iterable[dict]
    headers: list[str] | None = None


@dataclass(frozen=True)
class ConversationsReportFile:
    """
    File for the conversations report.

    Provide either in-memory ``content`` or an on-disk ``local_path`` for
    streaming uploads. Only one should be set.
    """

    name: str
    content: bytes | None = None
    local_path: str | None = None


@dataclass(frozen=True)
class AvailableReportWidgets:
    sections: list[str]
    custom_widgets: list[UUID]
    crosstab_widgets: list[UUID]
