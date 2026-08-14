from django.test import TestCase

from insights.metrics.ctwa.services import CTWADashboardService, MOCK_CTWA_DATA


class TestCTWADashboardService(TestCase):
    def test_get_data_returns_mock_contract(self):
        data = CTWADashboardService().get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data, MOCK_CTWA_DATA)
        self.assertIn("currency", data["attributed_revenue"])
        self.assertIn("value", data["attributed_revenue"])
        self.assertIn("avg", data["attributed_revenue"])
        self.assertIn("ctwa_conversations", data)
        self.assertIn("organic_conversations", data)
