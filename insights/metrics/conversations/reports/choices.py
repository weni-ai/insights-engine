from django.db.models import TextChoices


class ConversationsReportSections(TextChoices):
    RESOLUTIONS = "RESOLUTIONS"
    TRANSFERRED = "TRANSFERRED"
    TOPICS_AI = "TOPICS_AI"
    TOPICS_HUMAN = "TOPICS_HUMAN"
    CSAT_AI = "CSAT_AI"
    CSAT_HUMAN = "CSAT_HUMAN"
    NPS_AI = "NPS_AI"
    NPS_HUMAN = "NPS_HUMAN"
