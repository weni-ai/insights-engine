import pytest

from ..infra.repositories.memrepo import InMemoryUserRepository
from ..domain.entities import User
from ..app.usecases import CreateUserUseCase


class TestCreateUserUseCase:
    def setup_method(self) -> None:
        self.user_repo = InMemoryUserRepository()
        self.use_case = CreateUserUseCase(self.cast_member_repo)

    def test_invalid_input(self): ...
