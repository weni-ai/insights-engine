from django.db.models import TextChoices


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


class AbsoluteNumbersMetricsType(TextChoices):
    """
    Absolute numbers metrics type
    """

    TOTAL = "TOTAL"
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"
