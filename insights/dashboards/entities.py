from dataclasses import dataclass
from typing import Optional


@dataclass
class Dashboard:
    uuid: str
    project: str
    description: str
    is_default: str
    config: dict


@dataclass
class Widget:
    uuid: str
    dashboard: str
    description: str
    w_type: str
    source: str
    report: dict
    position: dict
    config: dict


@dataclass
class DashboardTemplate:
    uuid: str
    description: str
    project: Optional[str] = None
    setup: dict


@dataclass
class WidgetTemplate:
    uuid: str
    description: str
    project: Optional[str]
    setup: dict
