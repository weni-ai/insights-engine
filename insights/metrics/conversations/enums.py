from django.db.models import TextChoices


class CsatMetricsType(TextChoices):
    """
    Csat metrics type
    """

    AI = "AI"
    HUMAN = "HUMAN"
