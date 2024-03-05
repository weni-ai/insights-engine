from dataclasses import dataclass


@dataclass
class Project:
    uuid: str = None
    name: str = None
    timezone: str = None
    config: dict = None
    created_at: str = None
    updated_at: str = None


@dataclass
class Permission:
    uuid: str = None
    project: str = None
    user: str = None
    role: str = None
    created_at: str = None
    updated_at: str = None


@dataclass
class ChatSession:
    uuid: str = None
    permission: str = None
    session_id: str = None
    created_at: str = None
    updated_at: str = None
