from babel import numbers


class FormatTemplatesAndOrdersResponse:
    def execute(self, raw_metrics: dict) -> dict:
        template_metrics = raw_metrics["template_metrics"]
        orders_metrics = raw_metrics["orders_metrics"]

        currency_symbol = ""
        if currency_code := orders_metrics.get("revenue", {}).get("currency_code"):
            currency_symbol = numbers.get_currency_symbol(currency_code)

        return {
            "templates_metrics": {
                "sent": template_metrics["sent"],
                "delivered": template_metrics["delivered"],
                "read": template_metrics["read"],
                "clicked": template_metrics["clicked"],
            },
            "orders": {
                "revenue": {
                    "value": orders_metrics.get("revenue", {}).get("value", 0),
                    "currency_code": currency_symbol,
                    "increase_percentage": orders_metrics.get("revenue", {}).get(
                        "increase_percentage", 0.0
                    ),
                },
                "orders_placed": {
                    "value": orders_metrics.get("orders_placed", {}).get("value", 0),
                    "increase_percentage": orders_metrics.get("orders_placed", {}).get(
                        "increase_percentage", 0.0
                    ),
                },
            },
        }
