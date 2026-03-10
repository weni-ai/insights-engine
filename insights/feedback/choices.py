from django.db import models


class DashboardTypes(models.TextChoices):
    """
    This choice is used to define the type of dashboard.
    """

    CONVERSATIONAL = "CONVERSATIONAL"


class AnswerTypes(models.TextChoices):
    """
    This choice is used to define the type of form.
    """

    SCORE_1_5 = "SCORE_1_5"
    TEXT = "TEXT"


class ConversationalAnswerReferences(models.TextChoices):
    """
    This choice is used to define the reference of the answer.
    """

    TRUST = "TRUST"
    MAKE_DECISION = "MAKE_DECISION"
    ROI = "ROI"
    COMMENT = "COMMENT"
