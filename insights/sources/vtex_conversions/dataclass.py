from dataclasses import dataclass


@dataclass
class OrdersConversionsGraphDataField:
    """
    Dataclass to store orders conversions message status.
    """

    value: int = 0
    percentage: float = 0


@dataclass
class OrdersConversionsGraphData:
    """
    Dataclass to store orders conversions message metrics.
    """

    sent: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    delivered: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    read: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()
    clicked: OrdersConversionsGraphDataField = OrdersConversionsGraphDataField()


@dataclass
class OrdersConversions:
    """
    Dataclass to store orders conversions metrics.
    """

    graph_data: OrdersConversionsGraphData
