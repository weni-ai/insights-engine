from dataclasses import dataclass
from typing import List


@dataclass
class AbandonedCartWhatsAppTemplate:
    name: str
    ids: List[str | int]
