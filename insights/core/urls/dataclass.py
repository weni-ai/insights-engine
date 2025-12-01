from dataclasses import dataclass
from typing import Optional


@dataclass
class PaginationURLs:
    next_url: Optional[str]
    previous_url: Optional[str]
