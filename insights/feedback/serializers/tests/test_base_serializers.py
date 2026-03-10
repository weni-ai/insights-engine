from django.test import TestCase

from insights.feedback.serializers.base import (
    Score1To5AnswerSerializer,
    TextAnswerSerializer,
)


class TestScore1To5AnswerSerializer(TestCase):
    def test_validate_answer(self):
        serializer = Score1To5AnswerSerializer(
            data={"answer": "1", "type": "SCORE_1_5"}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["answer"], 1)

    def test_validate_answer_with_value_below_1(self):
        serializer = Score1To5AnswerSerializer(
            data={"answer": "0", "type": "SCORE_1_5"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["answer"][0].code, "invalid_answer")

    def test_validate_answer_with_value_above_5(self):
        serializer = Score1To5AnswerSerializer(
            data={"answer": "6", "type": "SCORE_1_5"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["answer"][0].code, "invalid_answer")

    def test_validate_answer_with_value_not_a_number(self):
        serializer = Score1To5AnswerSerializer(
            data={"answer": "abc", "type": "SCORE_1_5"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["answer"][0].code, "invalid_answer")

    def test_validate_answer_with_invalid_type(self):
        serializer = Score1To5AnswerSerializer(data={"answer": "1", "type": "INVALID"})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")


class TestTextAnswerSerializer(TestCase):
    def test_validate_answer(self):
        serializer = TextAnswerSerializer(data={"answer": "test", "type": "TEXT"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["answer"], "test")

    def test_validate_answer_with_invalid_type(self):
        serializer = TextAnswerSerializer(data={"answer": "test", "type": "INVALID"})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["type"][0].code, "invalid_choice")

    def test_validate_answer_with_invalid_answer(self):
        serializer = TextAnswerSerializer(
            data={"answer": "test" * 1001, "type": "TEXT"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["answer"][0].code, "invalid_answer")
