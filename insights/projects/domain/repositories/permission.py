from abc import ABC

from ....shared.domain.repositories import (
    BaseCreateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    BaseUpdateRepository,
    BaseListRepository,
)


class PermissionRepository(
    BaseCreateRepository,
    BaseUpdateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    BaseListRepository,
    ABC,
):
    pass
