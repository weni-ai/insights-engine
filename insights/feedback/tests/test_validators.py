from django.test import TestCase
from rest_framework import serializers

from insights.feedback.choices import DashboardTypes
from insights.feedback.validators import FeedbackDataValidator


class TestFeedbackDataValidator(TestCase):
    def test_validate_when_dashboard_type_is_invalid(self):
        validator = FeedbackDataValidator()
        data = {
            "answers": [
                {"reference": "TRUST", "answer": "1", "type": "SCORE_1_5"},
            ]
        }
        with self.assertRaises(serializers.ValidationError) as context:
            validator.validate("INVALID", data)

        self.assertEqual(context.exception.detail[0].code, "invalid_dashboard_type")

    def test_validate_when_reference_is_missing(self):
        validator = FeedbackDataValidator()
        data = {
            "answers": [
                {"answer": "1", "type": "SCORE_1_5"},
            ]
        }
        with self.assertRaises(serializers.ValidationError) as context:
            validator.validate(DashboardTypes.CONVERSATIONAL, data)

        self.assertEqual(context.exception.detail[0].code, "required")

    def test_validate_when_reference_is_not_unique(self):
        validator = FeedbackDataValidator()
        data = {
            "answers": [
                {"reference": "TRUST", "answer": "1", "type": "SCORE_1_5"},
                {"reference": "TRUST", "answer": "1", "type": "SCORE_1_5"},
            ]
        }

        with self.assertRaises(serializers.ValidationError) as context:
            validator.validate(DashboardTypes.CONVERSATIONAL, data)

        self.assertEqual(context.exception.detail[0].code, "unique")

    def test_validate_valid_conversational_data(self):
        validator = FeedbackDataValidator()
        data = {
            "answers": [
                {
                    "reference": "TRUST",
                    "answer": "1",
                    "type": "SCORE_1_5",
                },
                {"reference": "MAKE_DECISION", "answer": "1", "type": "SCORE_1_5"},
                {"reference": "ROI", "answer": "1", "type": "SCORE_1_5"},
                {"reference": "COMMENT", "answer": "test", "type": "TEXT"},
            ]
        }
        validator.validate(DashboardTypes.CONVERSATIONAL, data)
