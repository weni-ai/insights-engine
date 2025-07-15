from django.db import models


class ConversationsMetricsResource(models.TextChoices):
    TOPICS = "topics"
    SUBTOPICS = "subtopics"
