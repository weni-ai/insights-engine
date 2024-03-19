from dataclasses import dataclass, field
from typing import Optional

from ...shared.domain.entites import BaseEntity, UUIDEntity, DateEntity


@dataclass(slots=True, kw_only=True)
class Dashboard(BaseEntity, UUIDEntity, DateEntity):
    project: str
    description: str
    is_default: str
    config: dict

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Dashboard"


@dataclass(slots=True, kw_only=True)
class Widget(BaseEntity, UUIDEntity, DateEntity):
    dashboard: str
    description: str
    w_type: str
    source: str
    report: dict
    position: dict
    config: dict

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Widget"


@dataclass(slots=True, kw_only=True)
class DashboardTemplate(BaseEntity, UUIDEntity, DateEntity):
    description: str
    project: Optional[str] = None
    setup: dict

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Dashboard Template"


@dataclass(slots=True, kw_only=True)
class WidgetTemplate(BaseEntity, UUIDEntity, DateEntity):
    description: str
    project: Optional[str]
    setup: dict

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Widget Template"
