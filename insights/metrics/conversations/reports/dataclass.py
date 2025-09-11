from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationsReportWorksheet:
    """
    Worksheet for the conversations report.
    """

    name: str
    data: list[dict]
