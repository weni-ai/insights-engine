from dataclasses import dataclass, field
from datetime import datetime

from typing import Literal


from ...domain.entities import Permission
from ...domain.repositories import PermissionRepository


class CreatePermissionUseCase:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self.permission_repo = permission_repo

    def execute(self, permission=Permission) -> Permission:
        return self.permission_repo.create(permission)


@dataclass
class UpdatePermissionInput:
    role: int

    def __post_init__(self):
        self.updated_at = datetime.now()


class UpdatePermissionUseCase:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self.permission_repo = permission_repo

    def execute(self, uuid: str, fields: UpdatePermissionInput) -> Permission:
        return self.permission_repo.update(uuid=uuid, fields=fields.__dict__)


class DeletePermissionUseCase:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self.permission_repo = permission_repo

    def execute(self, uuid: str) -> bool:
        return self.permission_repo.delete(uuid=uuid)


class GetPermissionUseCase:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self.permission_repo = permission_repo

    def execute(self, uuid: str) -> bool:
        return self.permission_repo.get(uuid=uuid)


@dataclass(frozen=True, slots=True)
class PermissionListInput:
    project: str | None = field(default=None)
    user: str | None = field(default=None)
    role: int | None = field(default=None)


@dataclass
class PermissionListSearchInput:
    page: int | None = None
    per_page: int | None = None
    sort: str | None = None
    filter: PermissionListInput | None = None


@dataclass(frozen=True)
class PermissionListOutput:
    items: list[Permission]
    total: int
    current_page: int
    per_page: int
    last_page: int


class ListPermissionUseCase:
    def __init__(self, permission_repo: PermissionRepository) -> None:
        self.permission_repo = permission_repo

    def execute(self, filters: PermissionListInput) -> PermissionListOutput:
        return self.permission_repo.filter(filters=filters)
