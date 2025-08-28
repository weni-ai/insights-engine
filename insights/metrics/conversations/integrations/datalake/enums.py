from django.db import models


class DatalakeConversationsClassification(models.TextChoices):
    """
    Classification for conversations
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
