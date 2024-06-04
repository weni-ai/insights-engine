from dataclasses import dataclass


@dataclass(slots=True)
class AgentFieldSchema:
    status: str
    name: str
    active: int
    closed: int


@dataclass(slots=True)
class AgentFilterSchema:
    created_on__lte: str
    created_on__gte: str
