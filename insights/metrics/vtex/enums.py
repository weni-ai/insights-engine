from django.db.models import TextChoices


class OrdersSumGranularity(TextChoices):
    DAY = "day"
    WEEK = "week"


class WeekStartsOn(TextChoices):
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
