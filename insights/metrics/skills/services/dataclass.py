from dataclasses import dataclass
from typing import List


@dataclass
class AbandonedCartWhatsAppTemplate:
    name: str
    ids: List[str | int]


@dataclass
class AbandonedCartWabaTemplates:
    waba_id: str
    templates: List[AbandonedCartWhatsAppTemplate]
