from dataclasses import dataclass


@dataclass(frozen=True)
class CTWAConversionsData:
    conversations_started: int = 0
    conversations_qualified: int = 0
    conversations_converted: int = 0


@dataclass(frozen=True)
class CTWASummaryData:
    currency: str = ""
    attributed_revenue: float = 0
    avg_order_value: float = 0
    ctwa_conversations: int = 0
    organic_conversations: int = 0
