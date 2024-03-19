from typing import Optional

from ...domain.entities import User
from ...domain.repositories import UserRepository


class InMemoryUserRepository(UserRepository):
    memory = {}

    def flush(self) -> None:
        self.memory = {}

    def create(self, user: User) -> None:
        if self.memory.get(user.entity_id):
            raise ValueError(f"User {user.entity_id} already exists")
        self.memory[user.entity_id] = user

    def update(self, email: str, updated_fields: dict) -> None:
        updated_fields.pop("email", None)
        if not self.memory.get(email, None):
            raise ValueError(f"User {email} was not found")

        for field, value in updated_fields.items():
            # Maybe validate if the updated_fields are present in the entity,
            # if not throw an error "Entity has no field named {updated_field}"
            setattr(self.memory[email], field, value)

    def delete(self, email: str) -> bool:
        for existing_user in self._users:
            if existing_user.email == email:
                del existing_user
                return True

        raise ValueError(f"User {email} was not found")

    def get(self, email: str) -> Optional[User]:
        return self.memory.get(email)
