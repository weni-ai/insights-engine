from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from insights.feedback.choices import AnswerTypes, DashboardTypes
from insights.shared.models import BaseModel
from insights.dashboards.models import Dashboard
from insights.users.models import User


class Survey(BaseModel):
    start = models.DateTimeField(_("Start"))
    end = models.DateTimeField(_("End"))

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")

    def __str__(self):
        return f"{self.start} - {self.end}"

    @property
    def is_active(self) -> bool:
        return self.start <= timezone.now() <= self.end


class Feedback(BaseModel):
    survey = models.ForeignKey(
        Survey, verbose_name=_("Survey"), on_delete=models.CASCADE
    )
    dashboard = models.ForeignKey(
        Dashboard,
        verbose_name=_("Dashboard"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    dashboard_type = models.CharField(
        verbose_name=_("Dashboard type"), max_length=255, choices=DashboardTypes.choices
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")

    def __str__(self):
        return f"{self.survey} - {self.dashboard_type} - {self.user.email}"


class FeedbackAnswer(BaseModel):
    feedback = models.ForeignKey(
        Feedback,
        verbose_name=_("Feedback"),
        on_delete=models.CASCADE,
    )
    reference = models.CharField(
        verbose_name=_("Reference"),
        max_length=255,
    )
    answer = models.TextField(
        verbose_name=_("Answer"),
    )
    answer_type = models.CharField(
        verbose_name=_("Answer type"),
        max_length=255,
        choices=AnswerTypes.choices,
    )

    class Meta:
        verbose_name = _("Feedback answer")
        verbose_name_plural = _("Feedback answers")

    def __str__(self):
        return f"{self.feedback} - {self.reference} - {self.answer_type}"
