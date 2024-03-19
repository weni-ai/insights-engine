from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from ..domain.entities import User
from ..domain.repositories import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def execute(
        self, user: User
    ) -> (
        User
    ):  # receive a dto instead of a user instance, and instanciate it after to pass to the repo
        return self.user_repo.create(user)


@dataclass
class UpdateUserFields:
    first_name: Optional[str]
    last_name: Optional[str]
    can_communicate_externaly: Optional[bool] = None

    def __post_init__(self):
        self.updated_at = datetime.now()


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def execute(self, email: str, updated_fields: UpdateUserFields) -> User:
        updated_fields[""]
        return self.user_repo.update(email, updated_fields.__dict__)


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def execute(self, email: str) -> bool:
        return self.user_repo.delete(email)


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    def execute(self, email: str) -> User:
        return self.user_repo.get(email)
