from django.test import TestCase

from insights.metrics.templates_and_orders.usecases.format_templates_and_orders_response import (
    FormatTemplatesAndOrdersResponse,
)


class TestFormatTemplatesAndOrdersResponse(TestCase):
    def setUp(self):
        self.usecase = FormatTemplatesAndOrdersResponse()

    def test_formats_response_with_brl_currency(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 5,
                "delivered": 5,
                "read": 4,
                "clicked": 2,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 10100.10,
                    "currency_code": "BRL",
                    "increase_percentage": 100,
                },
                "orders_placed": {
                    "value": 100,
                    "increase_percentage": 100,
                },
            },
        }

        result = self.usecase.execute(raw_metrics)

        self.assertEqual(
            result["templates_metrics"],
            {"sent": 5, "delivered": 5, "read": 4, "clicked": 2},
        )
        self.assertEqual(result["orders"]["revenue"]["value"], 10100.10)
        self.assertEqual(result["orders"]["revenue"]["currency_code"], "R$")
        self.assertEqual(result["orders"]["revenue"]["increase_percentage"], 100)
        self.assertEqual(result["orders"]["orders_placed"]["value"], 100)
        self.assertEqual(
            result["orders"]["orders_placed"]["increase_percentage"], 100
        )

    def test_formats_response_with_usd_currency(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 10,
                "delivered": 8,
                "read": 5,
                "clicked": 3,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 1000.00,
                    "currency_code": "USD",
                    "increase_percentage": 50.0,
                },
                "orders_placed": {
                    "value": 10,
                    "increase_percentage": 25.0,
                },
            },
        }

        result = self.usecase.execute(raw_metrics)

        self.assertEqual(result["orders"]["revenue"]["currency_code"], "$")

    def test_returns_empty_string_when_no_currency_code(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 0,
                "delivered": 0,
                "read": 0,
                "clicked": 0,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 0,
                    "currency_code": "",
                    "increase_percentage": 0,
                },
                "orders_placed": {
                    "value": 0,
                    "increase_percentage": 0,
                },
            },
        }

        result = self.usecase.execute(raw_metrics)

        self.assertEqual(result["orders"]["revenue"]["currency_code"], "")

    def test_handles_missing_revenue_gracefully(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 5,
                "delivered": 3,
                "read": 2,
                "clicked": 1,
            },
            "orders_metrics": {},
        }

        result = self.usecase.execute(raw_metrics)

        self.assertEqual(result["orders"]["revenue"]["value"], 0)
        self.assertEqual(result["orders"]["revenue"]["currency_code"], "")
        self.assertEqual(result["orders"]["revenue"]["increase_percentage"], 0.0)
        self.assertEqual(result["orders"]["orders_placed"]["value"], 0)
        self.assertEqual(
            result["orders"]["orders_placed"]["increase_percentage"], 0.0
        )

    def test_preserves_template_metrics_values(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 150,
                "delivered": 120,
                "read": 80,
                "clicked": 45,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 50000.00,
                    "currency_code": "BRL",
                    "increase_percentage": 15.5,
                },
                "orders_placed": {
                    "value": 200,
                    "increase_percentage": 8.3,
                },
            },
        }

        result = self.usecase.execute(raw_metrics)

        self.assertEqual(result["templates_metrics"]["sent"], 150)
        self.assertEqual(result["templates_metrics"]["delivered"], 120)
        self.assertEqual(result["templates_metrics"]["read"], 80)
        self.assertEqual(result["templates_metrics"]["clicked"], 45)
