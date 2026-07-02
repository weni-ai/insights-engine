from babel import numbers


class FormatAbandonedCartSkillResponse:
    def execute(self, raw_metrics: dict) -> list[dict]:
        template_metrics = raw_metrics["template_metrics"]
        orders_metrics = raw_metrics["orders_metrics"]

        currency_symbol = ""
        if currency_code := orders_metrics.get("revenue", {}).get("currency_code"):
            currency_symbol = numbers.get_currency_symbol(currency_code)

        return [
            {
                "id": "sent-messages",
                "value": template_metrics["sent"],
            },
            {
                "id": "delivered-messages",
                "value": template_metrics["delivered"],
            },
            {
                "id": "read-messages",
                "value": template_metrics["read"],
            },
            {
                "id": "interactions",
                "value": template_metrics["clicked"],
            },
            {
                "id": "utm-revenue",
                "value": orders_metrics.get("revenue", {}).get("value", 0),
                "percentage": orders_metrics.get("revenue", {}).get(
                    "increase_percentage", 0.0
                ),
                "prefix": currency_symbol,
            },
            {
                "id": "orders-placed",
                "value": orders_metrics.get("orders_placed", {}).get("value", 0),
                "percentage": orders_metrics.get("orders_placed", {}).get(
                    "increase_percentage", 0.0
                ),
            },
        ]
