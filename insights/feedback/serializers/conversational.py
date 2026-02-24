from rest_framework import serializers


from insights.feedback.serializers.base import (
    Score1To5AnswerSerializer,
    TextAnswerSerializer,
)


class ConversationalFeedbackSerializer(serializers.Serializer):
    TRUST = Score1To5AnswerSerializer(required=True, allow_null=False)
    MAKE_DECISION = Score1To5AnswerSerializer(required=True, allow_null=False)
    ROI = Score1To5AnswerSerializer(required=True, allow_null=False)
    COMMENT = TextAnswerSerializer(required=False, allow_null=True)
