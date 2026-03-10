from typing import Optional
from uuid import UUID

from dataclasses import dataclass


@dataclass(frozen=True)
class SurveyStatus:
    """
    Survey status.
    """

    is_active: bool
    user_answered: bool
    uuid: Optional[UUID] = None
