from dataclasses import dataclass
from datetime import datetime

from ...domain.entities import ChatSession
from ...domain.repositories import ChatSessionRepository


class CreateChatSessionUseCase:
    def __init__(self, chatsession_repo: ChatSessionRepository) -> None:
        self.chatsession_repo = chatsession_repo

    def execute(self, project=ChatSession) -> ChatSession:
        return self.chatsession_repo.create(project)


@dataclass
class UpdateChatSessionInput:
    role: str

    def __post_init__(self):
        self.updated_at = datetime.now()


class UpdateChatSessionUseCase:
    def __init__(self, chatsession_repo: ChatSessionRepository) -> None:
        self.chatsession_repo = chatsession_repo

    def execute(self, uuid: str, fields: UpdateChatSessionInput) -> ChatSession:
        return self.chatsession_repo.update(uuid=uuid, fields=fields.__dict__)


class DeleteChatSessionUseCase:
    def __init__(self, chatsession_repo: ChatSessionRepository) -> None:
        self.chatsession_repo = chatsession_repo

    def execute(self, uuid: str) -> bool:
        return self.chatsession_repo.delete(uuid=uuid)


class GetChatSessionUseCase:
    def __init__(self, chatsession_repo: ChatSessionRepository) -> None:
        self.chatsession_repo = chatsession_repo

    def execute(self, uuid: str) -> bool:
        return self.chatsession_repo.get(uuid=uuid)
