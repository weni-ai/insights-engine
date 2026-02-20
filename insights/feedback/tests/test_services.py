from django.test import TestCase

from insights.feedback.services import FeedbackService


class TestFeedbackService(TestCase):
    def setUp(self):
        self.service = FeedbackService()
