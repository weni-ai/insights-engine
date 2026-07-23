from datetime import date
from unittest.mock import MagicMock, call

from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.meta.usecases.waba_migration_analytics import (
    ConsolidateWabaAnalyticsUseCase,
    WabaAnalyticsPeriod,
    merge_buttons_analytics,
    merge_messages_analytics,
    resolve_waba_analytics_periods,
)
from insights.projects.models import Project


class TestResolveWabaAnalyticsPeriods(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.current_waba_id = "new_waba"
        self.old_waba_id = "old_waba"
        self.migrated_at = "2026-03-15T12:00:00+00:00"

        Dashboard.objects.create(
            project=self.project,
            name="Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.current_waba_id,
                "migration_data": {
                    "waba_id": self.old_waba_id,
                    "migrated_at": self.migrated_at,
                },
            },
        )

    def test_returns_current_waba_when_no_migration_data(self):
        Dashboard.objects.all().delete()
        Dashboard.objects.create(
            project=self.project,
            name="Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.current_waba_id,
            },
        )

        periods = resolve_waba_analytics_periods(
            current_waba_id=self.current_waba_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        self.assertEqual(
            periods,
            [
                WabaAnalyticsPeriod(
                    waba_id=self.current_waba_id,
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 3, 31),
                )
            ],
        )

    def test_returns_only_old_waba_when_range_is_before_migration(self):
        periods = resolve_waba_analytics_periods(
            current_waba_id=self.current_waba_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        self.assertEqual(
            periods,
            [
                WabaAnalyticsPeriod(
                    waba_id=self.old_waba_id,
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 3, 10),
                )
            ],
        )

    def test_returns_only_new_waba_when_range_is_after_migration(self):
        periods = resolve_waba_analytics_periods(
            current_waba_id=self.current_waba_id,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 31),
        )

        self.assertEqual(
            periods,
            [
                WabaAnalyticsPeriod(
                    waba_id=self.current_waba_id,
                    start_date=date(2026, 3, 20),
                    end_date=date(2026, 3, 31),
                )
            ],
        )

    def test_splits_range_across_old_and_new_waba(self):
        periods = resolve_waba_analytics_periods(
            current_waba_id=self.current_waba_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        self.assertEqual(
            periods,
            [
                WabaAnalyticsPeriod(
                    waba_id=self.old_waba_id,
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 3, 14),
                ),
                WabaAnalyticsPeriod(
                    waba_id=self.current_waba_id,
                    start_date=date(2026, 3, 15),
                    end_date=date(2026, 3, 31),
                ),
            ],
        )


class TestMergeAnalyticsResponses(TestCase):
    def test_merge_messages_analytics_sums_status_and_data_points(self):
        responses = [
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 10},
                        "delivered": {"value": 8, "percentage": 80},
                        "read": {"value": 5, "percentage": 50},
                        "clicked": {"value": 2, "percentage": 20},
                    },
                    "data_points": [
                        {
                            "date": "2026-03-10",
                            "sent": 10,
                            "delivered": 8,
                            "read": 5,
                            "clicked": 2,
                        }
                    ],
                }
            },
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 20},
                        "delivered": {"value": 16, "percentage": 80},
                        "read": {"value": 10, "percentage": 50},
                        "clicked": {"value": 4, "percentage": 20},
                    },
                    "data_points": [
                        {
                            "date": "2026-03-20",
                            "sent": 20,
                            "delivered": 16,
                            "read": 10,
                            "clicked": 4,
                        }
                    ],
                }
            },
        ]

        merged = merge_messages_analytics(responses)

        self.assertEqual(merged["data"]["status_count"]["sent"]["value"], 30)
        self.assertEqual(merged["data"]["status_count"]["delivered"]["value"], 24)
        self.assertEqual(merged["data"]["status_count"]["delivered"]["percentage"], 80.0)
        self.assertEqual(len(merged["data"]["data_points"]), 2)
        self.assertEqual(merged["data"]["data_points"][0]["date"], "2026-03-10")
        self.assertEqual(merged["data"]["data_points"][1]["date"], "2026-03-20")

    def test_merge_messages_analytics_sums_same_date_points(self):
        responses = [
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 5},
                        "delivered": {"value": 5, "percentage": 100},
                        "read": {"value": 1, "percentage": 20},
                        "clicked": {"value": 0, "percentage": 0},
                    },
                    "data_points": [
                        {
                            "date": "2026-03-15",
                            "sent": 5,
                            "delivered": 5,
                            "read": 1,
                            "clicked": 0,
                        }
                    ],
                }
            },
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 7},
                        "delivered": {"value": 7, "percentage": 100},
                        "read": {"value": 2, "percentage": 28.57},
                        "clicked": {"value": 1, "percentage": 14.29},
                    },
                    "data_points": [
                        {
                            "date": "2026-03-15",
                            "sent": 7,
                            "delivered": 7,
                            "read": 2,
                            "clicked": 1,
                        }
                    ],
                }
            },
        ]

        merged = merge_messages_analytics(responses)

        self.assertEqual(merged["data"]["data_points"], [
            {
                "date": "2026-03-15",
                "sent": 12,
                "delivered": 12,
                "read": 3,
                "clicked": 1,
            }
        ])

    def test_merge_buttons_analytics_sums_totals(self):
        responses = [
            {
                "data": [
                    {
                        "label": "Continue",
                        "type": "QUICK_REPLY",
                        "total": 10,
                        "click_rate": 50.0,
                    }
                ]
            },
            {
                "data": [
                    {
                        "label": "Continue",
                        "type": "QUICK_REPLY",
                        "total": 5,
                        "click_rate": 25.0,
                    }
                ]
            },
        ]

        merged = merge_buttons_analytics(responses)

        self.assertEqual(len(merged["data"]), 1)
        self.assertEqual(merged["data"][0]["label"], "Continue")
        self.assertEqual(merged["data"][0]["total"], 15)


class TestConsolidateWabaAnalyticsUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.current_waba_id = "new_waba"
        self.old_waba_id = "old_waba"
        self.template_id = "template-1"

        Dashboard.objects.create(
            project=self.project,
            name="Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": self.current_waba_id,
                "migration_data": {
                    "waba_id": self.old_waba_id,
                    "migrated_at": "2026-03-15T12:00:00+00:00",
                },
            },
        )
        self.meta_client = MagicMock()
        self.usecase = ConsolidateWabaAnalyticsUseCase(self.meta_client)

    def test_calls_only_old_waba_for_pre_migration_range(self):
        self.meta_client.get_messages_analytics.return_value = {
            "data": {"status_count": {}, "data_points": []}
        }

        self.usecase.get_messages_analytics(
            waba_id=self.current_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        self.meta_client.get_messages_analytics.assert_called_once_with(
            waba_id=self.old_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
            include_data_points=True,
        )

    def test_calls_only_new_waba_for_post_migration_range(self):
        self.meta_client.get_messages_analytics.return_value = {
            "data": {"status_count": {}, "data_points": []}
        }

        self.usecase.get_messages_analytics(
            waba_id=self.current_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 31),
        )

        self.meta_client.get_messages_analytics.assert_called_once_with(
            waba_id=self.current_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 31),
            include_data_points=True,
        )

    def test_calls_both_wabas_and_merges_when_range_crosses_migration(self):
        self.meta_client.get_messages_analytics.side_effect = [
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 10},
                        "delivered": {"value": 10, "percentage": 100},
                        "read": {"value": 5, "percentage": 50},
                        "clicked": {"value": 1, "percentage": 10},
                    },
                    "data_points": [],
                }
            },
            {
                "data": {
                    "status_count": {
                        "sent": {"value": 20},
                        "delivered": {"value": 20, "percentage": 100},
                        "read": {"value": 10, "percentage": 50},
                        "clicked": {"value": 2, "percentage": 10},
                    },
                    "data_points": [],
                }
            },
        ]

        result = self.usecase.get_messages_analytics(
            waba_id=self.current_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            include_data_points=False,
        )

        self.assertEqual(
            self.meta_client.get_messages_analytics.call_args_list,
            [
                call(
                    waba_id=self.old_waba_id,
                    template_id=self.template_id,
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 3, 14),
                    include_data_points=False,
                ),
                call(
                    waba_id=self.current_waba_id,
                    template_id=self.template_id,
                    start_date=date(2026, 3, 15),
                    end_date=date(2026, 3, 31),
                    include_data_points=False,
                ),
            ],
        )
        self.assertEqual(result["data"]["status_count"]["sent"]["value"], 30)

    def test_buttons_analytics_calls_both_wabas_when_range_crosses_migration(self):
        self.meta_client.get_buttons_analytics.side_effect = [
            {
                "data": [
                    {
                        "label": "Continue",
                        "type": "QUICK_REPLY",
                        "total": 4,
                        "click_rate": 40.0,
                    }
                ]
            },
            {
                "data": [
                    {
                        "label": "Continue",
                        "type": "QUICK_REPLY",
                        "total": 6,
                        "click_rate": 30.0,
                    }
                ]
            },
        ]

        result = self.usecase.get_buttons_analytics(
            waba_id=self.current_waba_id,
            template_id=self.template_id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        self.assertEqual(self.meta_client.get_buttons_analytics.call_count, 2)
        self.assertEqual(result["data"][0]["total"], 10)
