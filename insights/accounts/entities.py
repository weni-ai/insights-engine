from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    uuid: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: str
    updated_at: str
