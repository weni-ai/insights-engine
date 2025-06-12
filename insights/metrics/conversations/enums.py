from django.db.models import TextChoices


class ConversationsTimeseriesUnit(TextChoices):
    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"
