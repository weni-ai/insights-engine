from django.db import models


class NexusResource(models.TextChoices):
    TOPICS = "topics"
    SUBTOPICS = "subtopics"
