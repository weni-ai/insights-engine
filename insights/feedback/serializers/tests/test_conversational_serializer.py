from django.test import TestCase

from insights.feedback.serializers.conversational import (
    ConversationalFeedbackSerializer,
)


class TestConversationalFeedbackSerializer(TestCase):
    def test_serializer(self):
        serializer = ConversationalFeedbackSerializer(
            data={
                "TRUST": {"answer": "1", "type": "SCORE_1_5"},
                "MAKE_DECISION": {"answer": "1", "type": "SCORE_1_5"},
                "ROI": {"answer": "1", "type": "SCORE_1_5"},
                "COMMENT": {"answer": "test", "type": "TEXT"},
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_serializer_with_invalid_data(self):
        serializer = ConversationalFeedbackSerializer(
            data={
                "TRUST": {"answer": "0", "type": "SCORE_1_5"},
                "MAKE_DECISION": {"answer": "6", "type": "SCORE_1_5"},
                "ROI": {"answer": "bla", "type": "SCORE_1_5"},
                "COMMENT": {"answer": "test" * 1001, "type": "TEXT"},
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["TRUST"]["answer"][0].code, "invalid_answer")
        self.assertEqual(
            serializer.errors["MAKE_DECISION"]["answer"][0].code, "invalid_answer"
        )
        self.assertEqual(serializer.errors["ROI"]["answer"][0].code, "invalid_answer")
        self.assertEqual(
            serializer.errors["COMMENT"]["answer"][0].code, "invalid_answer"
        )
