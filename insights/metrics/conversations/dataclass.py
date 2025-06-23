from dataclasses import dataclass


@dataclass
class NPS:
    """
    NPS is a metric that measures the Net Promoter Score of a product or service.
    """

    score: float
    total_responses: int
    promoters: int
    detractors: int
    passives: int
