import uuid as uuid_module

from abc import ABC, abstractproperty
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseEntity(ABC):
    @abstractproperty
    def entity_id(self) -> str:
        raise NotImplementedError

    @abstractproperty
    def verbose_name(self) -> str:
        raise NotImplementedError


@dataclass
class UUIDEntity:
    uuid: uuid_module.UUID = uuid_module.uuid4()


@dataclass
class DateEntity:
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
