from dataclasses import dataclass


@dataclass(frozen=True)
class OrdersConversionsUTMData:
    """
    Dataclass to store orders conversions UTM data.
    """

    count_sell: int = 0
    accumulated_total: float = 0
    medium_ticket: float = 0
    currency_code: str = ""


@dataclass(frozen=True)
class OrdersConversionsGraphDataField:
    """
    Dataclass to store orders conversions message status.
    """

    value: int = 0
    percentage: float = 0


@dataclass(frozen=True)
class OrdersConversionsGraphData:
    """
    Dataclass to store orders conversions message metrics.
    """

    sent: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    delivered: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    read: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    clicked: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    orders: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()


@dataclass(frozen=True)
class OrdersConversions:
    """
    Dataclass to store orders conversions metrics.
    """

    utm_data: OrdersConversionsUTMData
    graph_data: OrdersConversionsGraphData
