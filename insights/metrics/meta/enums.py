from enum import Enum


class AnalyticsGranularity(Enum):
    DAILY = "DAILY"


class MetricsTypes(Enum):
    CLICKED = "CLICKED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    SENT = "SENT"


class ProductType(Enum):
    CLOUD_API = "CLOUD_API"
    MM_LITE = "MARKETING_MESSAGES_LITE_API"
