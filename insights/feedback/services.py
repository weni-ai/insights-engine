from abc import ABC
from typing import Optional

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from insights.core.internal_domains import is_vtex_internal_domain
from insights.feedback.dataclass import SurveyStatus
from insights.feedback.validators import FeedbackDataValidator
from insights.users.models import User
from insights.dashboards.models import Dashboard
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from insights.feedback.models import Feedback, FeedbackAnswer, Survey
from insights.feedback.choices import DashboardTypes


class BaseFeedbackService(ABC):
    def get_current_survey(self) -> Optional[Survey]:
        raise NotImplementedError("Subclasses must implement this method")

    def get_survey_status(self, user: User, dashboard: Dashboard) -> SurveyStatus:
        raise NotImplementedError("Subclasses must implement this method")

    def create_feedback(
        self,
        user: User,
        dashboard: Dashboard,
        survey: Survey,
        dashboard_type: DashboardTypes,
        data: dict,
    ) -> Feedback:
        raise NotImplementedError("Subclasses must implement this method")


class FeedbackService(BaseFeedbackService):
    def __init__(self, validator: FeedbackDataValidator = FeedbackDataValidator()):
        self.validator = validator

    def get_current_survey(self) -> Optional[Survey]:
        """
        Get the current survey, if exists.
        """

        return Survey.objects.filter(
            start__lte=timezone.now(),
            end__gte=timezone.now(),
        ).first()

    def get_survey_status(self, user: User, dashboard: Dashboard) -> SurveyStatus:
        """
        Get the survey status for a user and a dashboard.
        """

        if is_vtex_internal_domain(user.email):
            return SurveyStatus(is_active=False, user_answered=False)

        current_survey = self.get_current_survey()

        if not current_survey:
            return SurveyStatus(is_active=False, user_answered=False)

        user_has_feedback = Feedback.objects.filter(
            survey=current_survey,
            user=user,
            dashboard=dashboard,
        ).exists()

        return SurveyStatus(
            is_active=True, user_answered=user_has_feedback, uuid=current_survey.uuid
        )

    def create_feedback(
        self,
        user: User,
        dashboard: Dashboard,
        survey: Survey,
        dashboard_type: DashboardTypes,
        data: dict,
    ):
        """
        Create a feedback for a user and a dashboard.
        """

        survey_status = self.get_survey_status(user, dashboard)

        if not survey_status.is_active:
            raise PermissionDenied(_("Survey is not active"))

        if survey_status.user_answered:
            raise PermissionDenied(_("User has already answered the survey"))

        validated_data = self.validator.validate(dashboard_type, data)

        with transaction.atomic():
            feedback = Feedback.objects.create(
                survey=survey,
                user=user,
                dashboard=dashboard,
                dashboard_type=dashboard_type,
            )

            feedback_answers = []

            for reference, answer in validated_data.items():
                answer_value = answer["answer"]
                if answer_value is None or answer_value == "":
                    continue

                feedback_answers.append(
                    FeedbackAnswer(
                        feedback=feedback,
                        reference=reference,
                        answer=answer_value,
                        answer_type=answer["type"],
                    )
                )

            FeedbackAnswer.objects.bulk_create(feedback_answers)

            return feedback
