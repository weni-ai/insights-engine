from django.db.models import TextChoices


class ConversationType(TextChoices):
    """
    Conversation type
    """

    HUMAN = "HUMAN"
    AI = "AI"
