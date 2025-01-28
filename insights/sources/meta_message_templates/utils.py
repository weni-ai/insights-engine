from datetime import datetime


def format_message_metrics_data(data: dict):
    dt = str(datetime.fromtimestamp(data.get("start")).date())

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


def format_button_metrics_data(buttons: list, data_points: list[dict]) -> dict:
    sent = 0
    buttons_data = {}

    for button in buttons:
        buttons_data[button.get("text")] = {"type": button.get("type"), "clicked": 0}

    for data in data_points:
        sent += data.get("sent")

        if not (clicked_buttons := data.get("clicked", None)):
            continue

        for btn in clicked_buttons:
            key = btn.get("button_content")

            if key not in buttons_data:
                continue

            buttons_data[key]["clicked"] += btn.get("count")

    response = []

    for key, btn_data in buttons_data.items():
        click_rate = 0 if sent == 0 else round((btn_data["clicked"] / sent) * 100, 2)

        btn = {
            "label": key,
            "type": btn_data.get("type"),
            "total": btn_data.get("clicked"),
            "click_rate": click_rate,
        }
        response.append(btn)

    return response
