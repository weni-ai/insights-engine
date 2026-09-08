from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class AverageOrderValueData:
    value: float
    currency_code: str = ""


class AverageOrderValueSource(Protocol):
    """
    Provides the average order value of human support rooms in a period.
    """

    def get_average_order_value(self, params: dict) -> AverageOrderValueData:
        raise NotImplementedError


class NullAverageOrderValueSource:
    """
    Used while assisted sales data has no origin to be read from.
    """

    def get_average_order_value(self, params: dict) -> AverageOrderValueData:
        return AverageOrderValueData(value=0.0)
