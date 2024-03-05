from dataclasses import dataclass
from typing import Optional


@dataclass
class PromptTemplate:
    uuid: str
    prompt: str
    description: str
    project: Optional[str] = None
    created_at: str
    updated_at: str
