from unittest.mock import MagicMock, patch

from django.test import TestCase

from insights.metrics.meta.usecases.get_project_wabas import GetProjectWabasUseCase
from insights.metrics.meta.usecases.get_templates_from_prefix import (
    GetTemplatesFromPrefixUseCase,
)
from insights.metrics.meta.usecases.get_templates_metrics_from_multiple_wabas import (
    GetTemplatesMetricsFromMultipleWabasUseCase,
    WabaTemplateIDs,
)
from insights.metrics.templates_and_orders.exceptions import (
    ErrorGettingOrdersMetrics,
)
from insights.metrics.templates_and_orders.usecases.get_templates_and_orders_metrics import (
    GetTemplatesAndOrdersMetrics,
)
from insights.projects.models import Project


class TestGetTemplatesAndOrdersMetrics(TestCase):
    def setUp(self):
        self.project = Project.objects.create()

        self.mock_get_wabas = MagicMock(spec=GetProjectWabasUseCase)
        self.mock_get_templates = MagicMock(spec=GetTemplatesFromPrefixUseCase)
        self.mock_get_metrics = MagicMock(
            spec=GetTemplatesMetricsFromMultipleWabasUseCase
        )

        self.usecase = GetTemplatesAndOrdersMetrics(
            get_project_wabas=self.mock_get_wabas,
            get_templates_from_prefix=self.mock_get_templates,
            get_templates_metrics=self.mock_get_metrics,
        )

        self.start_date = "2024-01-01"
        self.end_date = "2024-01-31"
        self.utm_source = "weniabandonedcart"
        self.template_name_prefix = "weni_abandoned_cart"

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_happy_path_combines_template_and_orders_metrics(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = ["waba_1", "waba_2"]
        self.mock_get_templates.execute.side_effect = [["t1", "t2"], ["t3"]]
        self.mock_get_metrics.execute.return_value = {
            "sent": 100,
            "delivered": 80,
            "read": 50,
            "clicked": 20,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {
                "value": 5000,
                "currency_code": "BRL",
                "increase_percentage": 10.5,
            },
            "orders_placed": {"value": 25, "increase_percentage": 5.0},
        }

        result = self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=self.template_name_prefix,
        )

        self.assertEqual(
            result["template_metrics"],
            {"sent": 100, "delivered": 80, "read": 50, "clicked": 20},
        )
        self.assertEqual(result["orders_metrics"]["revenue"]["value"], 5000)
        self.assertEqual(result["orders_metrics"]["orders_placed"]["value"], 25)

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_forwards_utm_source_to_orders_service(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = []
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 0, "currency_code": "", "increase_percentage": 0},
            "orders_placed": {"value": 0, "increase_percentage": 0},
        }

        custom_utm = "my_custom_utm"
        self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=custom_utm,
            template_name_prefix=self.template_name_prefix,
        )

        mock_orders_instance.get_metrics_from_utm_source.assert_called_once_with(
            utm_source=custom_utm,
            filters={
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
        )

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_forwards_template_name_prefix_to_get_templates(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = ["waba_1"]
        self.mock_get_templates.execute.return_value = ["t1"]
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 0, "currency_code": "", "increase_percentage": 0},
            "orders_placed": {"value": 0, "increase_percentage": 0},
        }

        custom_prefix = "weni_custom_skill"
        self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=custom_prefix,
        )

        self.mock_get_templates.execute.assert_called_once_with(
            waba_id="waba_1", prefix=custom_prefix
        )

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_no_wabas_returns_zeroed_template_metrics(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = []
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 1000, "currency_code": "BRL", "increase_percentage": 0},
            "orders_placed": {"value": 5, "increase_percentage": 0},
        }

        result = self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=self.template_name_prefix,
        )

        self.mock_get_templates.execute.assert_not_called()
        self.mock_get_metrics.execute.assert_called_once_with(
            waba_templates=[],
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertEqual(
            result["template_metrics"],
            {"sent": 0, "delivered": 0, "read": 0, "clicked": 0},
        )
        self.assertEqual(result["orders_metrics"]["revenue"]["value"], 1000)

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_no_templates_found_excludes_waba_from_list(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = ["waba_1", "waba_2"]
        self.mock_get_templates.execute.side_effect = [[], ["t1"]]
        self.mock_get_metrics.execute.return_value = {
            "sent": 10, "delivered": 8, "read": 5, "clicked": 2,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 0, "currency_code": "", "increase_percentage": 0},
            "orders_placed": {"value": 0, "increase_percentage": 0},
        }

        self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=self.template_name_prefix,
        )

        call_args = self.mock_get_metrics.execute.call_args
        waba_templates = call_args.kwargs["waba_templates"]
        self.assertEqual(len(waba_templates), 1)
        self.assertEqual(waba_templates[0].waba_id, "waba_2")
        self.assertEqual(waba_templates[0].template_ids, ["t1"])

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_all_wabas_without_templates_sends_empty_list(self, MockOrdersService):
        self.mock_get_wabas.execute.return_value = ["waba_1", "waba_2"]
        self.mock_get_templates.execute.return_value = []
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 0, "currency_code": "", "increase_percentage": 0},
            "orders_placed": {"value": 0, "increase_percentage": 0},
        }

        result = self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=self.template_name_prefix,
        )

        self.mock_get_metrics.execute.assert_called_once_with(
            waba_templates=[],
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertEqual(
            result["template_metrics"],
            {"sent": 0, "delivered": 0, "read": 0, "clicked": 0},
        )

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_orders_service_error_raises_error_getting_orders_metrics(
        self, MockOrdersService
    ):
        self.mock_get_wabas.execute.return_value = []
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.side_effect = Exception(
            "VTEX API error"
        )

        with self.assertRaises(ErrorGettingOrdersMetrics) as ctx:
            self.usecase.execute(
                project=self.project,
                start_date=self.start_date,
                end_date=self.end_date,
                utm_source=self.utm_source,
                template_name_prefix=self.template_name_prefix,
            )

        self.assertIn("Error getting orders from VTEX", str(ctx.exception))

    @patch(
        "insights.metrics.templates_and_orders.usecases"
        ".get_templates_and_orders_metrics.OrdersService"
    )
    def test_builds_waba_templates_correctly_for_multiple_wabas(
        self, MockOrdersService
    ):
        self.mock_get_wabas.execute.return_value = ["waba_a", "waba_b", "waba_c"]
        self.mock_get_templates.execute.side_effect = [
            ["t1", "t2"],
            [],
            ["t3"],
        ]
        self.mock_get_metrics.execute.return_value = {
            "sent": 0, "delivered": 0, "read": 0, "clicked": 0,
        }

        mock_orders_instance = MockOrdersService.return_value
        mock_orders_instance.get_metrics_from_utm_source.return_value = {
            "revenue": {"value": 0, "currency_code": "", "increase_percentage": 0},
            "orders_placed": {"value": 0, "increase_percentage": 0},
        }

        self.usecase.execute(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            utm_source=self.utm_source,
            template_name_prefix=self.template_name_prefix,
        )

        call_args = self.mock_get_metrics.execute.call_args
        waba_templates = call_args.kwargs["waba_templates"]

        self.assertEqual(len(waba_templates), 2)
        self.assertEqual(waba_templates[0].waba_id, "waba_a")
        self.assertEqual(waba_templates[0].template_ids, ["t1", "t2"])
        self.assertEqual(waba_templates[1].waba_id, "waba_c")
        self.assertEqual(waba_templates[1].template_ids, ["t3"])

    def test_defaults_to_real_usecase_instances_when_none_provided(self):
        usecase = GetTemplatesAndOrdersMetrics()

        self.assertIsInstance(usecase.get_project_wabas, GetProjectWabasUseCase)
        self.assertIsInstance(
            usecase.get_templates_from_prefix, GetTemplatesFromPrefixUseCase
        )
        self.assertIsInstance(
            usecase.get_templates_metrics,
            GetTemplatesMetricsFromMultipleWabasUseCase,
        )
