from django.test import TestCase

from insights.metrics.ctwa.integrations.datalake.dataclass import CTWAConversionsData
from insights.metrics.ctwa.integrations.datalake.services import (
    MOCK_CTWA_CONVERSIONS_DATA,
)
from insights.metrics.ctwa.services import CTWADashboardService, MOCK_CTWA_DATA


class MockCTWADatalakeService:
    def get_conversions_data(self, project_uuid, start_date, end_date, campaign=None):
        return MOCK_CTWA_CONVERSIONS_DATA


class TestCTWADashboardService(TestCase):
    def setUp(self):
        self.service = CTWADashboardService(
            datalake_service=MockCTWADatalakeService()
        )

    def test_get_data_returns_mock_contract(self):
        data = self.service.get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data, MOCK_CTWA_DATA)

    def test_get_conversions_maps_datalake_counts_to_funnel(self):
        data = self.service.get_conversions(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data["conversations_started"]["total"], 19400)
        self.assertEqual(data["conversations_started"]["percentage"], 100)
        self.assertEqual(data["conversations_qualified"]["total"], 7180)
        self.assertEqual(data["conversations_qualified"]["percentage"], 37.0)
        self.assertEqual(data["conversations_converted"]["total"], 2880)
        self.assertEqual(data["conversations_converted"]["percentage"], 14.8)

    def test_get_conversions_percentage_is_zero_when_started_is_zero(self):
        class EmptyDatalakeService:
            def get_conversions_data(self, **kwargs):
                return CTWAConversionsData()

        service = CTWADashboardService(datalake_service=EmptyDatalakeService())
        data = service.get_conversions(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data["conversations_started"]["percentage"], 100)
        self.assertEqual(data["conversations_qualified"]["percentage"], 0)
        self.assertEqual(data["conversations_converted"]["percentage"], 0)
