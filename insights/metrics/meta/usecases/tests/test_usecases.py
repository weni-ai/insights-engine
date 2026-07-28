from datetime import date
from unittest.mock import patch

from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.meta.enums import ProductType
from insights.metrics.meta.usecases.get_project_wabas import GetProjectWabasUseCase
from insights.metrics.meta.usecases.get_templates_from_prefix import (
    GetTemplatesFromPrefixUseCase,
)
from insights.metrics.meta.usecases.get_templates_metrics_from_multiple_wabas import (
    GetTemplatesMetricsFromMultipleWabasUseCase,
    WabaTemplateIDs,
)
from insights.projects.models import Project


class TestGetProjectWabasUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create()
        self.usecase = GetProjectWabasUseCase()

    def test_returns_waba_ids_from_whatsapp_dashboards(self):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_123"},
        )

        result = self.usecase.execute(self.project)

        self.assertEqual(result, ["waba_123"])

    def test_deduplicates_waba_ids(self):
        for i in range(3):
            Dashboard.objects.create(
                project=self.project,
                name=f"dash_{i}",
                description="",
                config={"is_whatsapp_integration": True, "waba_id": "waba_same"},
            )

        result = self.usecase.execute(self.project)

        self.assertEqual(result, ["waba_same"])

    def test_returns_multiple_distinct_waba_ids(self):
        Dashboard.objects.create(
            project=self.project,
            name="dash_a",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_a"},
        )
        Dashboard.objects.create(
            project=self.project,
            name="dash_b",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": "waba_b"},
        )

        result = self.usecase.execute(self.project)

        self.assertEqual(len(result), 2)
        self.assertIn("waba_a", result)
        self.assertIn("waba_b", result)

    def test_returns_empty_list_when_no_whatsapp_dashboards(self):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"some_other_key": True},
        )

        result = self.usecase.execute(self.project)

        self.assertEqual(result, [])

    def test_ignores_dashboards_with_missing_waba_id(self):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True},
        )

        result = self.usecase.execute(self.project)

        self.assertEqual(result, [])

    def test_ignores_dashboards_with_empty_waba_id(self):
        Dashboard.objects.create(
            project=self.project,
            name="dash",
            description="",
            config={"is_whatsapp_integration": True, "waba_id": ""},
        )

        result = self.usecase.execute(self.project)

        self.assertEqual(result, [])


class TestGetTemplatesFromPrefixUseCase(TestCase):
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_returns_template_ids_matching_prefix(self, mock_templates_list):
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t2"},
            ]
        }

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(waba_id="waba_123", prefix="weni_abandoned_cart")

        self.assertEqual(result, ["t1", "t2"])
        mock_templates_list.assert_called_once_with(
            waba_id="waba_123", name="weni_abandoned_cart"
        )

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_filters_out_templates_not_starting_with_prefix(self, mock_templates_list):
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_001", "id": "t1"},
                {"name": "other_weni_abandoned_cart", "id": "t2"},
                {"name": "weni_abandoned_cart_002", "id": "t3"},
                {"name": "totally_different", "id": "t4"},
            ]
        }

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(waba_id="waba_123", prefix="weni_abandoned_cart")

        self.assertEqual(result, ["t1", "t3"])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_returns_empty_list_when_no_templates_match(self, mock_templates_list):
        mock_templates_list.return_value = {
            "data": [
                {"name": "completely_different_template", "id": "t1"},
            ]
        }

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(waba_id="waba_123", prefix="weni_abandoned_cart")

        self.assertEqual(result, [])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_handles_empty_api_response(self, mock_templates_list):
        mock_templates_list.return_value = {"data": []}

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(waba_id="waba_123", prefix="weni_abandoned_cart")

        self.assertEqual(result, [])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_handles_missing_data_key(self, mock_templates_list):
        mock_templates_list.return_value = {}

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(waba_id="waba_123", prefix="weni_abandoned_cart")

        self.assertEqual(result, [])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_max_template_ids_caps_after_sorting_by_name_desc(
        self, mock_templates_list
    ):
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t2"},
                {"name": "weni_abandoned_cart_1700000050", "id": "t3"},
            ]
        }

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(
            waba_id="waba_123",
            prefix="weni_abandoned_cart",
            max_template_ids=2,
        )

        self.assertEqual(result, ["t2", "t3"])

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list")
    def test_max_template_ids_returns_all_when_under_limit(self, mock_templates_list):
        mock_templates_list.return_value = {
            "data": [
                {"name": "weni_abandoned_cart_1700000000", "id": "t1"},
                {"name": "weni_abandoned_cart_1700000100", "id": "t2"},
            ]
        }

        usecase = GetTemplatesFromPrefixUseCase()
        result = usecase.execute(
            waba_id="waba_123",
            prefix="weni_abandoned_cart",
            max_template_ids=5,
        )

        self.assertEqual(result, ["t2", "t1"])


class TestGetTemplatesMetricsFromMultipleWabasUseCase(TestCase):
    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_aggregates_metrics_from_single_waba(self, mock_analytics):
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 10, "delivered": 8, "read": 5, "clicked": 2},
                    {"sent": 5, "delivered": 4, "read": 3, "clicked": 1},
                ]
            }
        }

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        result = usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id="waba_123", template_ids=["t1", "t2"]),
            ],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # 2 product types x (10+5, 8+4, 5+3, 2+1) = doubled
        self.assertEqual(result["sent"], 30)
        self.assertEqual(result["delivered"], 24)
        self.assertEqual(result["read"], 16)
        self.assertEqual(result["clicked"], 6)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_aggregates_metrics_from_multiple_wabas(self, mock_analytics):
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 10, "delivered": 8, "read": 5, "clicked": 2},
                ]
            }
        }

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        result = usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id="waba_a", template_ids=["t1"]),
                WabaTemplateIDs(waba_id="waba_b", template_ids=["t2"]),
            ],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # 2 WABAs x 2 product types = 4 calls, each returning (10, 8, 5, 2)
        self.assertEqual(mock_analytics.call_count, 4)
        self.assertEqual(result["sent"], 40)
        self.assertEqual(result["delivered"], 32)
        self.assertEqual(result["read"], 20)
        self.assertEqual(result["clicked"], 8)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_calls_both_product_types(self, mock_analytics):
        mock_analytics.return_value = {
            "data": {"data_points": [{"sent": 1, "delivered": 1, "read": 1, "clicked": 1}]}
        }

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id="waba_123", template_ids=["t1"]),
            ],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        product_types = {call.kwargs["product_type"] for call in mock_analytics.call_args_list}
        self.assertEqual(
            product_types,
            {ProductType.CLOUD_API.value, ProductType.MM_LITE.value},
        )

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_chunks_template_ids_per_request(self, mock_analytics):
        mock_analytics.return_value = {
            "data": {"data_points": [{"sent": 1, "delivered": 1, "read": 1, "clicked": 1}]}
        }

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        template_ids = [str(i) for i in range(25)]

        usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id="waba_123", template_ids=template_ids),
            ],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # 25 IDs / 10 per chunk = 3 chunks, x2 product types = 6 calls
        self.assertEqual(mock_analytics.call_count, 6)

        cloud_api_calls = [
            call
            for call in mock_analytics.call_args_list
            if call.kwargs["product_type"] == ProductType.CLOUD_API.value
        ]
        self.assertEqual(len(cloud_api_calls[0].kwargs["template_id"]), 10)
        self.assertEqual(len(cloud_api_calls[1].kwargs["template_id"]), 10)
        self.assertEqual(len(cloud_api_calls[2].kwargs["template_id"]), 5)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_returns_zeroed_dict_when_no_data_points(self, mock_analytics):
        mock_analytics.return_value = {"data": {"data_points": []}}

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        result = usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id="waba_123", template_ids=["t1"]),
            ],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        self.assertEqual(result, {"sent": 0, "delivered": 0, "read": 0, "clicked": 0})

    def test_returns_zeroed_dict_when_no_waba_templates(self):
        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        result = usecase.execute(
            waba_templates=[],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        self.assertEqual(result, {"sent": 0, "delivered": 0, "read": 0, "clicked": 0})

    def _create_migrated_dashboard(
        self,
        *,
        current_waba_id: str,
        old_waba_id: str,
        migrated_at: str = "2026-03-15T12:00:00+00:00",
    ):
        project = Project.objects.create(name="Migration Project")
        Dashboard.objects.create(
            project=project,
            name="Meta dashboard",
            config={
                "is_whatsapp_integration": True,
                "waba_id": current_waba_id,
                "migration_data": {
                    "waba_id": old_waba_id,
                    "migrated_at": migrated_at,
                },
            },
        )
        return project

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_queries_only_old_waba_when_range_is_before_migration(
        self, mock_analytics
    ):
        current_waba_id = "new_waba"
        old_waba_id = "old_waba"
        self._create_migrated_dashboard(
            current_waba_id=current_waba_id,
            old_waba_id=old_waba_id,
        )
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 10, "delivered": 8, "read": 5, "clicked": 2},
                ]
            }
        }

        with (
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview"
            ) as mock_preview,
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list"
            ) as mock_list,
        ):
            mock_preview.return_value = {"name": "weni_abandoned_cart"}
            mock_list.return_value = {
                "data": [{"name": "weni_abandoned_cart", "id": "old_t1"}]
            }

            usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
            result = usecase.execute(
                waba_templates=[
                    WabaTemplateIDs(
                        waba_id=current_waba_id, template_ids=["new_t1"]
                    ),
                ],
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 10),
            )

        self.assertEqual(mock_analytics.call_count, 2)  # 2 product types
        for call in mock_analytics.call_args_list:
            self.assertEqual(call.kwargs["waba_id"], old_waba_id)
            self.assertEqual(call.kwargs["template_id"], ["old_t1"])
            self.assertEqual(call.kwargs["start_date"], date(2026, 3, 1))
            self.assertEqual(call.kwargs["end_date"], date(2026, 3, 10))

        self.assertEqual(result["sent"], 20)
        self.assertEqual(result["delivered"], 16)
        self.assertEqual(result["read"], 10)
        self.assertEqual(result["clicked"], 4)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_queries_only_current_waba_when_range_is_after_migration(
        self, mock_analytics
    ):
        current_waba_id = "new_waba"
        old_waba_id = "old_waba"
        self._create_migrated_dashboard(
            current_waba_id=current_waba_id,
            old_waba_id=old_waba_id,
        )
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 7, "delivered": 6, "read": 4, "clicked": 1},
                ]
            }
        }

        usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
        result = usecase.execute(
            waba_templates=[
                WabaTemplateIDs(waba_id=current_waba_id, template_ids=["new_t1"]),
            ],
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 31),
        )

        self.assertEqual(mock_analytics.call_count, 2)
        for call in mock_analytics.call_args_list:
            self.assertEqual(call.kwargs["waba_id"], current_waba_id)
            self.assertEqual(call.kwargs["template_id"], ["new_t1"])

        self.assertEqual(result["sent"], 14)
        self.assertEqual(result["delivered"], 12)
        self.assertEqual(result["read"], 8)
        self.assertEqual(result["clicked"], 2)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_queries_both_wabas_when_range_crosses_migration(self, mock_analytics):
        current_waba_id = "new_waba"
        old_waba_id = "old_waba"
        self._create_migrated_dashboard(
            current_waba_id=current_waba_id,
            old_waba_id=old_waba_id,
        )
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 10, "delivered": 8, "read": 5, "clicked": 2},
                ]
            }
        }

        with (
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview"
            ) as mock_preview,
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list"
            ) as mock_list,
        ):
            mock_preview.return_value = {"name": "weni_abandoned_cart"}
            mock_list.return_value = {
                "data": [{"name": "weni_abandoned_cart", "id": "old_t1"}]
            }

            usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
            result = usecase.execute(
                waba_templates=[
                    WabaTemplateIDs(
                        waba_id=current_waba_id, template_ids=["new_t1"]
                    ),
                ],
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
            )

        # 2 periods x 2 product types
        self.assertEqual(mock_analytics.call_count, 4)

        old_calls = [
            call
            for call in mock_analytics.call_args_list
            if call.kwargs["waba_id"] == old_waba_id
        ]
        new_calls = [
            call
            for call in mock_analytics.call_args_list
            if call.kwargs["waba_id"] == current_waba_id
        ]
        self.assertEqual(len(old_calls), 2)
        self.assertEqual(len(new_calls), 2)

        for call in old_calls:
            self.assertEqual(call.kwargs["template_id"], ["old_t1"])
            self.assertEqual(call.kwargs["start_date"], date(2026, 3, 1))
            self.assertEqual(call.kwargs["end_date"], date(2026, 3, 15))

        for call in new_calls:
            self.assertEqual(call.kwargs["template_id"], ["new_t1"])
            self.assertEqual(call.kwargs["start_date"], date(2026, 3, 15))
            self.assertEqual(call.kwargs["end_date"], date(2026, 3, 31))

        # 4 calls x (10, 8, 5, 2)
        self.assertEqual(result["sent"], 40)
        self.assertEqual(result["delivered"], 32)
        self.assertEqual(result["read"], 20)
        self.assertEqual(result["clicked"], 8)

    @patch("insights.metrics.meta.clients.MetaGraphAPIClient.get_messages_analytics")
    def test_skips_old_waba_when_old_template_cannot_be_resolved(
        self, mock_analytics
    ):
        current_waba_id = "new_waba"
        old_waba_id = "old_waba"
        self._create_migrated_dashboard(
            current_waba_id=current_waba_id,
            old_waba_id=old_waba_id,
        )
        mock_analytics.return_value = {
            "data": {
                "data_points": [
                    {"sent": 3, "delivered": 2, "read": 1, "clicked": 0},
                ]
            }
        }

        with (
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_template_preview"
            ) as mock_preview,
            patch(
                "insights.metrics.meta.clients.MetaGraphAPIClient.get_templates_list"
            ) as mock_list,
        ):
            mock_preview.return_value = {"name": "weni_abandoned_cart_new"}
            mock_list.return_value = {"data": []}

            usecase = GetTemplatesMetricsFromMultipleWabasUseCase()
            result = usecase.execute(
                waba_templates=[
                    WabaTemplateIDs(
                        waba_id=current_waba_id, template_ids=["new_t1"]
                    ),
                ],
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
            )

        # Only current WABA period (old skipped) x 2 product types
        self.assertEqual(mock_analytics.call_count, 2)
        for call in mock_analytics.call_args_list:
            self.assertEqual(call.kwargs["waba_id"], current_waba_id)

        self.assertEqual(result["sent"], 6)
        self.assertEqual(result["delivered"], 4)
        self.assertEqual(result["read"], 2)
        self.assertEqual(result["clicked"], 0)
