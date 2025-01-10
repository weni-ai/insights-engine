from datetime import datetime


def format_message_metrics_data(data: dict):
    dt = datetime.fromtimestamp(data.get("start")).date()

    return {
        "date": dt,
        "sent": data.get("sent"),
        "delivered": data.get("sent"),
        "read": data.get("read"),
        "clicked": sum([btn.get("count", 0) for btn in data.get("clicked", [])]),
    }


def format_messages_metrics_data_points(data_points: list[dict]):
    results = []

    for data in data_points:
        results.append(format_message_metrics_data(data))

    return results
