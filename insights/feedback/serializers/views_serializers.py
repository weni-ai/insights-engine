from rest_framework import serializers

from insights.feedback.choices import DashboardTypes
from insights.feedback.models import Feedback, FeedbackAnswer


class CheckSurveyQueryParamsSerializer(serializers.Serializer):
    project_uuid = serializers.UUIDField(required=True)
    dashboard = serializers.UUIDField(required=True)


class CheckSurveyResponseSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)
    user_answered = serializers.BooleanField(required=True)
    uuid = serializers.UUIDField(required=False, allow_null=True)


class CreateFeedbackSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=DashboardTypes.choices, required=True)
    dashboard = serializers.UUIDField(required=True)
    survey = serializers.UUIDField(required=True)
    answers = serializers.ListField(child=serializers.DictField(), required=True)


class AnswerSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="answer_type")

    class Meta:
        model = FeedbackAnswer
        fields = ["reference", "answer", "type"]


class CreateFeedbackResponseSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="dashboard_type")
    dashboard = serializers.UUIDField(source="dashboard.uuid")
    survey = serializers.UUIDField(source="survey.uuid")
    answers = AnswerSerializer(source="feedbackanswer_set.all", many=True)

    class Meta:
        model = Feedback
        fields = ["uuid", "type", "dashboard", "survey", "answers"]
