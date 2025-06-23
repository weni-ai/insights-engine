from django.db import models


class NPSType(models.TextChoices):
    """
    NPS type
    """

    AI = "AI"
    HUMAN = "HUMAN"
