from abc import ABC
from typing import Optional

from insights.core.internal_domains import is_vtex_internal_domain
from insights.feedback.dataclass import SurveyStatus
from insights.users.models import User
from insights.dashboards.models import Dashboard
from django.utils import timezone

from insights.feedback.models import Feedback, Survey


class BaseFeedbackService(ABC):
    def get_current_survey(self) -> Optional[Survey]:
        raise NotImplementedError("Subclasses must implement this method")

    def get_survey_status(self, user: User, dashboard: Dashboard) -> SurveyStatus:
        raise NotImplementedError("Subclasses must implement this method")


class FeedbackService(BaseFeedbackService):
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
