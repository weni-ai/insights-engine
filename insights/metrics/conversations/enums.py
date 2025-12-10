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


class AvailableWidgets(TextChoices):
    """
    Available widgets
    """

    SALES_FUNNEL = "SALES_FUNNEL"
