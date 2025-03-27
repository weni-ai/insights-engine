from enum import Enum


class AnalyticsGranularity(Enum):
    DAILY = "DAILY"


class MetricsTypes(Enum):
    CLICKED = "CLICKED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    SENT = "SENT"
