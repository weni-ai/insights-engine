from dataclasses import dataclass, field

from ...shared.domain.entites import BaseEntity, UUIDEntity, DateEntity


@dataclass(slots=True, kw_only=True)
class Project(BaseEntity, UUIDEntity, DateEntity):
    name: str
    timezone: str
    config: dict = field(default_factory=dict)

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Project"


@dataclass(slots=True, kw_only=True)
class Permission(BaseEntity, UUIDEntity, DateEntity):
    project: str
    user: str
    role: str

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Permission"


@dataclass(slots=True, kw_only=True)
class ChatSession(BaseEntity, UUIDEntity, DateEntity):
    permission: str
    session_id: str

    @property
    def entity_id(self) -> str:
        return str(self.uuid)

    @property
    def verbose_name(self) -> str:
        return "Chat Session"
