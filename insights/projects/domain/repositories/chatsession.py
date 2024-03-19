from abc import ABC

from ....shared.domain.repositories import (
    BaseCreateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    BaseUpdateRepository,
)


class ChatSessionRepository(
    BaseCreateRepository,
    BaseUpdateRepository,
    BaseDeleteRepository,
    BaseGetRepository,
    ABC,
):
    pass
