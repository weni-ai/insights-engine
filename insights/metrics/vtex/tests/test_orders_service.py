from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project


class TestOrdersService(TestCase):
    def setUp(self):
        self.project = Project.objects.create()
        self.service = OrdersService(self.project)

    def test_get_past_dates(self):
        start_date = timezone.now() - timedelta(days=10)
        end_date = timezone.now() - timedelta(days=5)

        past_start_date, past_end_date = self.service._get_past_dates(
            start_date, end_date
        )

        self.assertEqual(
            past_start_date.date(), timezone.now().date() - timedelta(days=15)
        )
        self.assertEqual(
            past_end_date.date(), timezone.now().date() - timedelta(days=10)
        )

    def test_calculate_increase_percentage(self):
        past_value = 100
        current_value = 150

        increase_percentage = self.service._calculate_increase_percentage(
            past_value, current_value
        )

        self.assertEqual(increase_percentage, 50.0)
