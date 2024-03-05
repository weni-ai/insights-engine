from dataclasses import dataclass


@dataclass
class PromptTemplate:
    uuid: str = None
    text: str = None
    created_at: str = None
    updated_at: str = None
