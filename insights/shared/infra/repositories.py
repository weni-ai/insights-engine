from abc import ABC, abstractclassmethod

from typing import Optional

from ..domain.entites import BaseEntity


class BaseInMemoryRepository:
    memory = {}

    def flush(self) -> None:
        self.memory = {}

    def create(self, entity: BaseEntity) -> None:
        if self.memory.get(entity.entity_id):
            raise ValueError(f"{entity.verbose_name} {entity.entity_id} already exists")
        self.memory[entity.entity_id] = entity

    def update(self, identifier: str, updated_fields: dict) -> None:
        if not self.memory.get(identifier, None):
            raise ValueError(f"User {identifier} was not found")

        for field, value in updated_fields.items():
            # Maybe validate if the updated_fields are present in the entity,
            # if not throw an error "Entity has no field named {updated_field}"
            setattr(self.memory[identifier], field, value)

    def delete(self, email: str) -> bool:
        for existing_user in self._users:
            if existing_user.email == email:
                del existing_user
                return True

        raise ValueError(f"User {email} was not found")

    def get(self, identifier: str) -> Optional[BaseEntity]:
        return self.memory.get(identifier)
