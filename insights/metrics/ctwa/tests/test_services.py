from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.metrics.ctwa.integrations.datalake.dataclass import CTWAConversionsData
from insights.metrics.ctwa.integrations.datalake.services import CTWADatalakeService
from insights.metrics.ctwa.services import CTWADashboardService


SAMPLE_ROWS = [
    {
        "campaign_source": "120250777996740371",
        "conversation_started": 3200,
        "lead_qualified": 1450,
        "purchase_completed": 520,
        "order_value": 509600,
    },
    {
        "campaign_source": "120250777996750371",
        "conversation_started": 2100,
        "lead_qualified": 780,
        "purchase_completed": 210,
        "order_value": 134400,
    },
    {
        "campaign_source": "weekend",
        "conversation_started": 7400,
        "lead_qualified": 2650,
        "purchase_completed": 1180,
        "order_value": 212400,
    },
    {
        "campaign_source": "store",
        "conversation_started": 4100,
        "lead_qualified": 1180,
        "purchase_completed": 430,
        "order_value": 64500,
    },
    {
        "campaign_source": "black-friday",
        "conversation_started": 2600,
        "lead_qualified": 1120,
        "purchase_completed": 540,
        "order_value": 113400,
    },
]


def _fake_ctwa_by_campaign(**params):
    rows = SAMPLE_ROWS
    campaign_source = params.get("campaign_source")
    if campaign_source:
        rows = [row for row in rows if row["campaign_source"] == campaign_source]
    return {"values": rows}


def _fake_totals(*args, **kwargs):
    return ConversationsTotalsMetrics(
        total_conversations=ConversationsTotalsMetric(value=42200, percentage=100),
        resolved=ConversationsTotalsMetric(value=0, percentage=0),
        unresolved=ConversationsTotalsMetric(value=0, percentage=0),
        transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
    )


class EmptyConversionsDatalakeService:
    def get_conversions_data(self, **kwargs):
        return CTWAConversionsData()


class TestCTWADashboardService(TestCase):
    def setUp(self):
        self.service = CTWADashboardService(
            datalake_service=CTWADatalakeService(
                ctwa_by_campaign_client=_fake_ctwa_by_campaign,
                conversations_totals_getter=_fake_totals,
            )
        )

    def test_get_data_aggregates_all_campaigns(self):
        data = self.service.get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-20",
            end_date="2026-08-26",
        )

        self.assertEqual(data["ctwa_conversations"], 19400)
        self.assertEqual(data["attributed_revenue"]["value"], 1034300)
        self.assertEqual(data["attributed_revenue"]["avg"], 359)
        self.assertEqual(data["organic_conversations"], 22800)
        self.assertEqual(data["attributed_revenue"]["currency"], "USD")

    def test_get_data_filters_by_campaign_source(self):
        data = self.service.get_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-20",
            end_date="2026-08-26",
            campaign="120250777996740371",
        )

        self.assertEqual(data["ctwa_conversations"], 3200)
        self.assertEqual(data["attributed_revenue"]["value"], 509600)
        self.assertEqual(data["organic_conversations"], 22800)

    def test_get_conversions_maps_datalake_counts_to_funnel(self):
        data = self.service.get_conversions(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-20",
            end_date="2026-08-26",
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
            start_date="2026-08-20",
            end_date="2026-08-26",
        )

        self.assertEqual(data["conversations_started"]["percentage"], 100)
        self.assertEqual(data["conversations_qualified"]["percentage"], 0)
        self.assertEqual(data["conversations_converted"]["percentage"], 0)

    def test_fetch_rows_sends_inclusive_datetime_bounds(self):
        captured = {}

        def capture_client(**params):
            captured.update(params)
            return {"values": SAMPLE_ROWS}

        service = CTWADatalakeService(
            ctwa_by_campaign_client=capture_client,
            conversations_totals_getter=_fake_totals,
        )
        service.get_performance_by_campaign(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-18",
            end_date="2026-08-19",
        )

        self.assertEqual(captured["dt_start"], "2026-08-19 00:00:00")
        self.assertEqual(captured["dt_end"], "2026-08-19 23:59:59")
        self.assertNotIn("date_start", captured)
        self.assertNotIn("date_end", captured)

    def test_clamps_start_date_to_ctwa_floor(self):
        captured = {}
        totals_dates = {}

        def capture_client(**params):
            captured.update(params)
            return {"values": SAMPLE_ROWS}

        def capture_totals(**kwargs):
            totals_dates.update(kwargs)
            return _fake_totals()

        service = CTWADatalakeService(
            ctwa_by_campaign_client=capture_client,
            conversations_totals_getter=capture_totals,
        )
        service.get_summary_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-13",
            end_date="2026-08-21",
        )

        self.assertEqual(captured["dt_start"], "2026-08-19 00:00:00")
        self.assertEqual(captured["dt_end"], "2026-08-21 23:59:59")
        self.assertEqual(
            totals_dates["start_date"].date().isoformat(), "2026-08-19"
        )
        self.assertEqual(
            totals_dates["end_date"].date().isoformat(), "2026-08-21"
        )

    def test_does_not_clamp_start_date_after_floor(self):
        captured = {}

        def capture_client(**params):
            captured.update(params)
            return {"values": SAMPLE_ROWS}

        service = CTWADatalakeService(
            ctwa_by_campaign_client=capture_client,
            conversations_totals_getter=_fake_totals,
        )
        service.get_performance_by_campaign(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-21",
            end_date="2026-08-28",
        )

        self.assertEqual(captured["dt_start"], "2026-08-21 00:00:00")
        self.assertEqual(captured["dt_end"], "2026-08-28 23:59:59")

    def test_returns_empty_when_range_ends_before_floor(self):
        calls = []

        def capture_client(**params):
            calls.append(params)
            return {"values": SAMPLE_ROWS}

        data = CTWADatalakeService(
            ctwa_by_campaign_client=capture_client,
            conversations_totals_getter=_fake_totals,
        ).get_summary_data(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-06",
            end_date="2026-08-12",
        )

        self.assertEqual(calls, [])
        self.assertEqual(data.ctwa_conversations, 0)
        self.assertEqual(data.organic_conversations, 0)

    def test_get_performance_by_campaign_paginates(self):
        data = self.service.get_performance_by_campaign(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-20",
            end_date="2026-08-26",
            limit=2,
            offset=0,
        )

        self.assertEqual(data["count"], 5)
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["campaign"], "weekend")
        self.assertNotIn("uuid", data["results"][0])

    def test_get_performance_by_campaign_filters_by_campaign_source(self):
        data = self.service.get_performance_by_campaign(
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            start_date="2026-08-20",
            end_date="2026-08-26",
            campaign="120250777996740371",
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["campaign"], "120250777996740371")
        self.assertEqual(data["results"][0]["conversations"], 3200)
