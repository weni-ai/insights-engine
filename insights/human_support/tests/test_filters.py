from datetime import date
from uuid import uuid4

from django.test import TestCase

from insights.human_support.filters import HumanSupportFilterSet
from insights.projects.models import Project


class TestHumanSupportFilterSetAverageOrderValue(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )

    def _cleaned(self, data):
        filterset = HumanSupportFilterSet(
            data=data,
            queryset=Project.objects.none(),
        )
        self.assertTrue(filterset.form.is_valid(), filterset.form.errors)
        return filterset.apply_project_timezone(self.project)

    def test_covers_dashboard_and_comparison_filters_without_widget_params(self):
        sector_uuid = str(uuid4())
        queue_uuid = str(uuid4())
        tag_uuid = str(uuid4())

        result = self._cleaned(
            {
                "sectors": [sector_uuid],
                "queues": [queue_uuid],
                "tags": [tag_uuid],
                "channels": ["whatsapp"],
                "agent": "agent@example.com",
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "comparison_start_date": "2025-03-01",
                "comparison_end_date": "2025-03-31",
            }
        )

        self.assertEqual([str(value) for value in result["sectors"]], [sector_uuid])
        self.assertEqual([str(value) for value in result["queues"]], [queue_uuid])
        self.assertEqual([str(value) for value in result["tags"]], [tag_uuid])
        self.assertEqual(result["channels"], ["whatsapp"])
        self.assertEqual(result["agent"], "agent@example.com")
        self.assertEqual(result["start_date"].date(), date(2025, 4, 1))
        self.assertEqual(result["end_date"].date(), date(2025, 4, 30))
        self.assertEqual(result["comparison_start_date"].date(), date(2025, 3, 1))
        self.assertEqual(result["comparison_end_date"].date(), date(2025, 3, 31))

    def test_localizes_comparison_dates_in_project_timezone(self):
        result = self._cleaned(
            {
                "comparison_start_date": "2025-03-01",
                "comparison_end_date": "2025-03-31",
            }
        )

        start = result["comparison_start_date"]
        end = result["comparison_end_date"]

        self.assertEqual(str(start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(end.tzinfo), "America/Sao_Paulo")
        self.assertEqual((start.hour, start.minute, start.second), (0, 0, 0))
        self.assertEqual((end.hour, end.minute, end.second), (23, 59, 59))

    def test_localizes_period_dates_in_project_timezone(self):
        result = self._cleaned(
            {
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
            }
        )

        start = result["start_date"]
        end = result["end_date"]

        self.assertEqual(str(start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(end.tzinfo), "America/Sao_Paulo")
        self.assertEqual((start.hour, start.minute, start.second), (0, 0, 0))
        self.assertEqual((end.hour, end.minute, end.second), (23, 59, 59))

    def test_does_not_require_comparison_dates(self):
        result = self._cleaned({"start_date": "2025-04-01", "end_date": "2025-04-30"})

        self.assertNotIn("comparison_start_date", result)
        self.assertNotIn("comparison_end_date", result)
