from django.test import TestCase

from insights.metrics.skills.usecases.format_abandoned_cart_skill_response import (
    FormatAbandonedCartSkillResponse,
)


class TestFormatAbandonedCartSkillResponse(TestCase):
    def setUp(self):
        self.formatter = FormatAbandonedCartSkillResponse()

    def test_formats_template_and_orders_metrics_into_skill_response(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 100,
                "delivered": 80,
                "read": 50,
                "clicked": 20,
            },
            "orders_metrics": {
                "revenue": {
                    "value": 5000,
                    "currency_code": "BRL",
                    "increase_percentage": 10.5,
                },
                "orders_placed": {"value": 25, "increase_percentage": 5.0},
            },
        }

        result = self.formatter.execute(raw_metrics)

        self.assertEqual(
            result,
            [
                {"id": "sent-messages", "value": 100},
                {"id": "delivered-messages", "value": 80},
                {"id": "read-messages", "value": 50},
                {"id": "interactions", "value": 20},
                {
                    "id": "utm-revenue",
                    "value": 5000,
                    "percentage": 10.5,
                    "prefix": "R$",
                },
                {
                    "id": "orders-placed",
                    "value": 25,
                    "percentage": 5.0,
                },
            ],
        )

    def test_handles_missing_orders_fields_with_defaults(self):
        raw_metrics = {
            "template_metrics": {
                "sent": 0,
                "delivered": 0,
                "read": 0,
                "clicked": 0,
            },
            "orders_metrics": {},
        }

        result = self.formatter.execute(raw_metrics)

        self.assertEqual(result[4]["value"], 0)
        self.assertEqual(result[4]["percentage"], 0.0)
        self.assertEqual(result[4]["prefix"], "")
        self.assertEqual(result[5]["value"], 0)
        self.assertEqual(result[5]["percentage"], 0.0)
