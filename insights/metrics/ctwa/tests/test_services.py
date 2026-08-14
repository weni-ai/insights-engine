from django.test import TestCase

from insights.metrics.ctwa.integrations.datalake.dataclass import CTWAConversionsData
from insights.metrics.ctwa.integrations.datalake.services import CTWADatalakeService
from insights.metrics.ctwa.mocks import MOCK_CAMPAIGNS_PERFORMANCE
from insights.metrics.ctwa.services import CTWADashboardService


class EmptyConversionsDatalakeService:
    def get_conversions_data(self, **kwargs):
        return CTWAConversionsData()


class TestCTWADashboardService(TestCase):
    def setUp(self):
        self.service = CTWADashboardService(datalake_service=CTWADatalakeService())

    def test_get_data_aggregates_all_campaigns(self):
        data = self.service.get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data["ctwa_conversations"], 19400)
        self.assertEqual(data["attributed_revenue"]["value"], 1034300)
        self.assertEqual(data["attributed_revenue"]["avg"], 359)
        self.assertEqual(data["organic_conversations"], 22800)

    def test_get_data_filters_by_campaign_uuid(self):
        campaign_uuid = MOCK_CAMPAIGNS_PERFORMANCE[0]["uuid"]
        data = self.service.get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
            campaign=campaign_uuid,
        )

        self.assertEqual(data["ctwa_conversations"], 3200)
        self.assertEqual(data["attributed_revenue"]["value"], 509600)

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
        service = CTWADashboardService(
            datalake_service=EmptyConversionsDatalakeService()
        )
        data = service.get_conversions(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(data["conversations_started"]["percentage"], 100)
        self.assertEqual(data["conversations_qualified"]["percentage"], 0)
        self.assertEqual(data["conversations_converted"]["percentage"], 0)

    def test_get_performance_by_campaign_paginates(self):
        data = self.service.get_performance_by_campaign(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
            limit=2,
            offset=0,
        )

        self.assertEqual(data["count"], 5)
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["campaign"], "Contractor Bulk Pricing")
        self.assertNotIn("uuid", data["results"][0])
