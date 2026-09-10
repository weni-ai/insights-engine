from datetime import date
from uuid import uuid4

from django.test import TestCase

from insights.human_support.filters import HumanSupportFilterSet
from insights.projects.models import Project


class HumanSupportFilterSetTestCase(TestCase):
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
        cleaned = filterset.apply_project_timezone(self.project)
        return {
            key: value for key, value in cleaned.items() if value not in (None, [], "")
        }


class TestHumanSupportFilterSetAverageOrderValue(HumanSupportFilterSetTestCase):
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


class TestHumanSupportFilterSetSalesFunnel(HumanSupportFilterSetTestCase):
    def test_covers_dashboard_filters_without_widget_params(self):
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
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
            }
        )

        self.assertEqual([str(value) for value in result["sectors"]], [sector_uuid])
        self.assertEqual([str(value) for value in result["queues"]], [queue_uuid])
        self.assertEqual([str(value) for value in result["tags"]], [tag_uuid])
        self.assertEqual(result["channels"], ["whatsapp"])
        self.assertEqual(result["agent"], "agent@example.com")
        self.assertEqual(result["start_date"].date(), date(2026, 8, 1))
        self.assertEqual(result["end_date"].date(), date(2026, 8, 7))
        self.assertNotIn("comparison_start_date", result)
        self.assertNotIn("comparison_end_date", result)

    def test_localizes_period_dates_in_project_timezone(self):
        result = self._cleaned(
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
            }
        )

        start = result["start_date"]
        end = result["end_date"]

        self.assertEqual(str(start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(end.tzinfo), "America/Sao_Paulo")
        self.assertEqual((start.hour, start.minute, start.second), (0, 0, 0))
        self.assertEqual((end.hour, end.minute, end.second), (23, 59, 59))


class TestHumanSupportFilterSetChannelRevenueSale(HumanSupportFilterSetTestCase):
    def test_covers_dashboard_filters_and_metric_without_widget_params(self):
        sector_uuid = str(uuid4())
        queue_uuid = str(uuid4())
        tag_uuid = str(uuid4())

        result = self._cleaned(
            {
                "sectors": [sector_uuid],
                "queues": [queue_uuid],
                "tags": [tag_uuid],
                "channels": ["whatsapp", "others"],
                "agent": "agent@example.com",
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "metric": "sale",
            }
        )

        self.assertEqual([str(value) for value in result["sectors"]], [sector_uuid])
        self.assertEqual([str(value) for value in result["queues"]], [queue_uuid])
        self.assertEqual([str(value) for value in result["tags"]], [tag_uuid])
        self.assertEqual(result["channels"], ["whatsapp", "others"])
        self.assertEqual(result["agent"], "agent@example.com")
        self.assertEqual(result["start_date"].date(), date(2026, 8, 1))
        self.assertEqual(result["end_date"].date(), date(2026, 8, 7))
        self.assertEqual(result["metric"], "sale")
        self.assertNotIn("comparison_start_date", result)
        self.assertNotIn("comparison_end_date", result)

    def test_accepts_revenue_metric(self):
        result = self._cleaned({"metric": "revenue"})

        self.assertEqual(result["metric"], "revenue")

    def test_does_not_require_metric(self):
        result = self._cleaned({"start_date": "2026-08-01", "end_date": "2026-08-07"})

        self.assertNotIn("metric", result)

    def test_localizes_period_dates_in_project_timezone(self):
        result = self._cleaned(
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
            }
        )

        start = result["start_date"]
        end = result["end_date"]

        self.assertEqual(str(start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(end.tzinfo), "America/Sao_Paulo")
        self.assertEqual((start.hour, start.minute, start.second), (0, 0, 0))
        self.assertEqual((end.hour, end.minute, end.second), (23, 59, 59))


class TestHumanSupportFilterSetPerformanceByRepresentative(
    HumanSupportFilterSetTestCase
):
    def test_covers_dashboard_comparison_and_ordering_filters(self):
        sector_uuid = str(uuid4())
        queue_uuid = str(uuid4())
        tag_uuid = str(uuid4())

        result = self._cleaned(
            {
                "sectors": [sector_uuid],
                "queues": [queue_uuid],
                "tags": [tag_uuid],
                "channels": ["whatsapp"],
                "agent": "emma@example.com",
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "comparison_start_date": "2026-07-25",
                "comparison_end_date": "2026-07-31",
                "ordering": "-revenue",
                "page_size": 10,
            }
        )

        self.assertEqual([str(value) for value in result["sectors"]], [sector_uuid])
        self.assertEqual([str(value) for value in result["queues"]], [queue_uuid])
        self.assertEqual([str(value) for value in result["tags"]], [tag_uuid])
        self.assertEqual(result["channels"], ["whatsapp"])
        self.assertEqual(result["agent"], "emma@example.com")
        self.assertEqual(result["start_date"].date(), date(2026, 8, 1))
        self.assertEqual(result["end_date"].date(), date(2026, 8, 7))
        self.assertEqual(result["comparison_start_date"].date(), date(2026, 7, 25))
        self.assertEqual(result["comparison_end_date"].date(), date(2026, 7, 31))
        self.assertEqual(result["ordering"], "-revenue")
        self.assertEqual(result["page_size"], 10)

    def test_localizes_period_and_comparison_dates(self):
        result = self._cleaned(
            {
                "start_date": "2026-08-01",
                "end_date": "2026-08-07",
                "comparison_start_date": "2026-07-25",
                "comparison_end_date": "2026-07-31",
            }
        )

        start = result["start_date"]
        end = result["end_date"]
        comparison_start = result["comparison_start_date"]
        comparison_end = result["comparison_end_date"]

        self.assertEqual(str(start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(end.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(comparison_start.tzinfo), "America/Sao_Paulo")
        self.assertEqual(str(comparison_end.tzinfo), "America/Sao_Paulo")
        self.assertEqual((start.hour, start.minute, start.second), (0, 0, 0))
        self.assertEqual((end.hour, end.minute, end.second), (23, 59, 59))
        self.assertEqual(
            (comparison_start.hour, comparison_start.minute, comparison_start.second),
            (0, 0, 0),
        )
        self.assertEqual(
            (comparison_end.hour, comparison_end.minute, comparison_end.second),
            (23, 59, 59),
        )
