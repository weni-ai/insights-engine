from enum import Enum


class Operations(Enum):
    LIST_TEMPLATES = "list_templates"
    TEMPLATE_PREVIEW = "template_preview"
    MESSAGES_ANALYTICS = "messages_analytics"
    BUTTONS_ANALYTICS = "buttons_analytics"


class AnalyticsGranularity(Enum):
    DAILY = "DAILY"


class MetricsTypes(Enum):
    CLICKED = "CLICKED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    SENT = "SENT"
