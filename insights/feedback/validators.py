from abc import ABC
from insights.feedback.choices import DashboardTypes


class BaseFeedbackDataValidator(ABC):
    def validate(self, dashboard_type: DashboardTypes, data: dict):
        raise NotImplementedError("Subclasses must implement this method")


class ConversationalFeedbackDataValidator(BaseFeedbackDataValidator):
    pass
