from rest_framework import serializers


from insights.feedback.serializers.base import (
    Score1To5AnswerSerializer,
    TextAnswerSerializer,
)


class ConversationalFeedbackSerializer(serializers.Serializer):
    TRUST = Score1To5AnswerSerializer()
    MAKE_DECISION = Score1To5AnswerSerializer()
    ROI = Score1To5AnswerSerializer()
    COMMENT = TextAnswerSerializer()
