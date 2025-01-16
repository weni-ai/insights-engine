from datetime import datetime


def format_message_metrics_data(data: dict):
    dt = datetime.fromtimestamp(data.get("start")).date()

    return {
        "date": dt,
        "sent": data.get("sent"),
        "delivered": data.get("delivered"),
        "read": data.get("read"),
        "clicked": sum([btn.get("count", 0) for btn in data.get("clicked", [])]),
    }


def format_messages_metrics_data(data: dict) -> dict:
    data_points: dict = data.get("data_points", [])

    status_count = {
        "sent": {
            "value": 0,
        },
        "delivered": {
            "value": 0,
        },
        "read": {
            "value": 0,
        },
        "clicked": {
            "value": 0,
        },
    }
    formatted_data_points = []

    for data in data_points:
        result = format_message_metrics_data(data)

        formatted_data_points.append(result)

        for status in ("sent", "delivered", "read", "clicked"):
            status_count[status]["value"] += result.get(status)

    for status in ("delivered", "read", "clicked"):
        status_count[status]["percentage"] = round(
            (status_count[status]["value"] / status_count["sent"]["value"]) * 100, 2
        )

    return {"status_count": status_count, "data_points": formatted_data_points}
