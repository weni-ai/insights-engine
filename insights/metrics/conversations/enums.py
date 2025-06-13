from django.db.models import TextChoices


class ConversationsSubjectsType(TextChoices):
    """
    Enum for conversations subjects type
    """

    GENERAL = "GENERAL"
    HUMAN = "HUMAN"
