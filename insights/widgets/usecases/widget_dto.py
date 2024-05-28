from dataclasses import dataclass
from typing import Dict, Union


@dataclass
class WidgetCreationDTO:
    dashboard: str
    name: str
    w_type: str
    source: str
    position: Dict[str, int]
    config: Dict[str, Union[str, int, float, bool, None]]
    report: Dict[str, Union[str, int, float, bool, None]]
