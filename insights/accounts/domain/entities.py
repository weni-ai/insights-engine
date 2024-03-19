import re

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from .exceptions import UserValidationException


@dataclass
class User:
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    can_communicate_externaly: bool = False
    created_at: datetime = datetime.now()  # pay attention to the timezone
    updated_at: datetime = datetime.now()

    def __post_init__(self):
        return self._validate_email(self.email)

    def _validate_email(self, email: str):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise UserValidationException(
                "ERROR: {'field': 'email', 'detail': 'Invalid email, please inform a valid email.'}"
            )

    @property
    def entity_id(self):
        return self.email
