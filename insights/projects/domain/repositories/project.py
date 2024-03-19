from abc import ABC

from ....shared.domain.repositories import (
    BaseCreateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    BaseUpdateRepository,
)


class ProjectRepository(
    BaseCreateRepository,
    BaseUpdateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    ABC,
):
    pass
