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
