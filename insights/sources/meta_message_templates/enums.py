from enum import Enum


class Operations(Enum):
    TEMPLATE_PREVIEW = "template_preview"
    MESSAGES_ANALYTICS = "messages_analytics"
    BUTTONS_ANALYTICS = "buttonS_analytics"


class AnalyticsGranularity(Enum):
    DAILY = "DAILY"


class MetricsTypes(Enum):
    CLICKED = "CLICKED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    SENT = "SENT"
