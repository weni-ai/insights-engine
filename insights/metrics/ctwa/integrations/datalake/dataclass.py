from dataclasses import dataclass


@dataclass(frozen=True)
class CTWAConversionsData:
    conversations_started: int = 0
    conversations_qualified: int = 0
    conversations_converted: int = 0
