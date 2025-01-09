from enum import Enum


class Operations(Enum):
    MESSAGES_ANALYTICS = "messages_analytics"


class AnalyticsGranularity(Enum):
    DAILY = "DAILY"


class MetricsTypes(Enum):
    CLICKED = "CLICKED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    SENT = "SENT"
