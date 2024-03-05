import re

from dataclasses import dataclass
from typing import Optional

from .exceptions import UserValidationException


@dataclass
class User:
    uuid: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: str
    updated_at: str

    def __post_init__(self):
        return self._validate_email(self.email)

    def _validate_email(email: str):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise UserValidationException(
                "ERROR: {'field': 'email', 'detail': 'Invalid email, please inform an valid email.'}"
            )
