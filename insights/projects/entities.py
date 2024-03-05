from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    uuid: str
    name: str
    timezone: str
    config: Optional[dict] = None
    created_at: str
    updated_at: str


@dataclass
class Permission:
    uuid: str
    project: str
    user: str
    role: str
    created_at: str
    updated_at: str


@dataclass
class ChatSession:
    uuid: str
    permission: str
    session_id: str
    created_at: str
    updated_at: str
