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


class CsatMetricsType(TextChoices):
    """
    Csat metrics type
    """

    AI = "AI"
    HUMAN = "HUMAN"


class NpsMetricsType(TextChoices):
    """
    Nps metrics type
    """

    AI = "AI"
    HUMAN = "HUMAN"


class ConversationType(TextChoices):
    """
    Conversation type
    """

    HUMAN = "HUMAN"
    AI = "AI"


class ConversationsMetricsResource(TextChoices):
    TOPICS = "topics"
    SUBTOPICS = "subtopics"


class AvailableWidgetsListType(TextChoices):
    """
    Available widgets list type
    """

    NATIVE = "NATIVE"
    CUSTOM = "CUSTOM"


class AvailableWidgets(TextChoices):
    """
    Available widgets
    """

    SALES_FUNNEL = "SALES_FUNNEL"
