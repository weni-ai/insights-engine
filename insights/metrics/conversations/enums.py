from django.db.models import TextChoices


class ConversationsTimeseriesUnit(TextChoices):
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"


class ConversationsSubjectsType(TextChoices):
    """
    Enum for conversations subjects type
    """

    GENERAL = "GENERAL"
    HUMAN = "HUMAN"


class NPSType(TextChoices):
    """
    NPS type
    """

    AI = "AI"
    HUMAN = "HUMAN"


class ConversationsMetricsResource(TextChoices):
    TOPICS = "topics"
    SUBTOPICS = "subtopics"


class ConversationType(TextChoices):
    """
    Conversation type
    """

    HUMAN = "HUMAN"
    AI = "AI"
